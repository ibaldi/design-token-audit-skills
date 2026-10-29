import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROPERTIES = ROOT / "skills" / "claude" / "token-readonly-scan" / "scripts" / "collect_figma_properties.js"
VARIABLES = ROOT / "skills" / "claude" / "token-readonly-scan" / "scripts" / "collect_figma_variables.js"


def run_collector(path: Path, mode_from: str, mode_to: str, figma_source: str) -> dict:
    source = path.read_text(encoding="utf-8").replace(f'mode: "{mode_from}"', f'mode: "{mode_to}"', 1)
    harness = f"""
const source = {json.dumps(source)};
const figma = {figma_source};
const run = new Function("figma", "return (async function() {{\\n" + source + "\\n}}).call(null);");
run(figma).then(value => process.stdout.write(JSON.stringify(value))).catch(error => {{
  process.stderr.write(error.stack || String(error));
  process.exit(1);
}});
"""
    result = subprocess.run(["node", "-e", harness], capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


@unittest.skipUnless(shutil.which("node"), "Node.js is required for collector regression tests")
class FigmaCollectorTests(unittest.TestCase):
    def test_property_collector_preserves_remote_stale_and_unresolved_references(self) -> None:
        figma = """{
          fileKey: "fixture-file",
          root: {name: "Fixture", children: [{
            id: "Page:1", name: "Page", loadAsync: async () => {}, children: [
              {id: "Node:1", name: "Remote", type: "FRAME", opacity: 1, boundVariables: {opacity: {id: "Remote:1"}}},
              {id: "Node:2", name: "Stale", type: "FRAME", opacity: 1, boundVariables: {opacity: {id: "Stale:1"}}},
              {id: "Node:3", name: "Missing", type: "FRAME", opacity: 1, boundVariables: {opacity: {id: "Missing:1"}}},
              {id: "Node:4", name: "Failed", type: "FRAME", opacity: 1, boundVariables: {opacity: {id: "Failed:1"}}},
              {id: "Node:5", name: "Duplicate", type: "FRAME", opacity: 1, boundVariables: {opacity: {id: "Remote:1"}}}
            ]
          }]},
          variables: {
            getLocalVariablesAsync: async () => [],
            getVariableByIdAsync: async id => {
              if (id === "Remote:1") return {id, remote: true, name: "space/xs", key: "remote-key", resolvedType: "FLOAT", variableCollectionId: "RemoteCollection:1"};
              if (id === "Stale:1") return {id, remote: false, name: "old/local", key: "stale-key", resolvedType: "FLOAT", variableCollectionId: "Collection:old"};
              if (id === "Missing:1") return null;
              throw new Error("not accessible");
            }
          }
        }"""
        chunk = run_collector(PROPERTIES, "page_inventory", "pages", figma)
        references = {item["id"]: item for item in chunk["referenced_variables"]}
        self.assertEqual(len(references), 4)
        self.assertEqual(references["Remote:1"]["origin"], "remote_library")
        self.assertEqual(references["Remote:1"]["collection_id"], "RemoteCollection:1")
        self.assertEqual(references["Stale:1"]["origin"], "stale_local_reference")
        self.assertEqual(references["Missing:1"]["origin"], "unresolved_reference")
        self.assertEqual(references["Failed:1"]["origin"], "unresolved_reference")

    def test_variable_collector_normalizes_composite_color(self) -> None:
        figma = """{
          fileKey: "fixture-file",
          root: {name: "Fixture"},
          variables: {
            getLocalVariableCollectionsAsync: async () => [{
              id: "Collection:1", name: "Colors", defaultModeId: "Mode:1",
              modes: [{modeId: "Mode:1", name: "Default"}], variableIds: ["Variable:overlay"],
              remote: false, hiddenFromPublishing: false
            }],
            getVariableByIdAsync: async id => ({
              id, name: "overlay", variableCollectionId: "Collection:1", resolvedType: "COLOR",
              description: "", scopes: [], remote: false, hiddenFromPublishing: false, codeSyntax: {},
              valuesByMode: {"Mode:1": {color: {type: "VARIABLE_ALIAS", id: "Variable:color"}, opacity: {type: "VARIABLE_ALIAS", id: "Variable:opacity"}}}
            })
          }
        }"""
        chunk = run_collector(VARIABLES, "inventory", "variables", figma)
        value = chunk["variables"][0]["values_by_mode"]["Mode:1"]
        self.assertEqual(value["kind"], "composite")
        self.assertEqual(value["components"]["color"]["target_variable_id"], "Variable:color")
        self.assertEqual(value["components"]["opacity"]["target_variable_id"], "Variable:opacity")


if __name__ == "__main__":
    unittest.main()
