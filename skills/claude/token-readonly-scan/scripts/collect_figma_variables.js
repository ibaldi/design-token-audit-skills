// collect_figma_variables.js — token-readonly-scan 0.9.0
// READ ONLY. Run as the body of a Figma Plugin API / figma_execute call.
// Change CONFIG only. The returned chunks are normalized by assemble_snapshot.py.

const CONFIG = {
  mode: "inventory", // "inventory" | "variables"
  collectionIds: [], // variables mode: one or a few collection IDs; [] means all
  startByCollection: {}, // resume a large collection: {"VariableCollectionId:...": 2000}
  maxVariables: 2000
};

const ADAPTER_ID = "figma-console-plugin-api";
const ADAPTER_VERSION = "0.9.0";

async function normalizeValue(value) {
  if (value && typeof value === "object" && value.type === "VARIABLE_ALIAS") {
    try {
      const target = await figma.variables.getVariableByIdAsync(value.id);
      if (target && target.remote) {
        return { kind: "not_observable", reason: "remote alias target is outside the local inventory", target_variable_id: value.id };
      }
    } catch (_) {
      return { kind: "not_observable", reason: "alias target could not be read", target_variable_id: value.id };
    }
    return { kind: "alias", target_variable_id: value.id };
  }
  if (value && typeof value === "object" && "r" in value && "g" in value && "b" in value) {
    return {
      kind: "literal",
      value: { r: value.r, g: value.g, b: value.b, a: "a" in value ? value.a : 1 }
    };
  }
  if (value && typeof value === "object" && "color" in value && "opacity" in value) {
    // COLOR value that combines a color and a separate opacity, each possibly an alias.
    return {
      kind: "composite",
      components: {
        color: await normalizeValue(value.color),
        opacity: await normalizeValue(value.opacity)
      }
    };
  }
  return { kind: "literal", value };
}

function collectionRecord(collection) {
  return {
    id: collection.id,
    name: collection.name,
    default_mode_id: collection.defaultModeId,
    modes: collection.modes.map((mode, position) => ({
      id: mode.modeId,
      name: mode.name,
      position
    })),
    variable_ids: collection.variableIds.slice(),
    remote: !!collection.remote,
    hidden_from_publishing: !!collection.hiddenFromPublishing
  };
}

async function variableRecord(variable, collection) {
  const values = {};
  for (const mode of collection.modes) {
    if (!(mode.modeId in variable.valuesByMode)) {
      values[mode.modeId] = { kind: "missing" };
    } else {
      values[mode.modeId] = await normalizeValue(variable.valuesByMode[mode.modeId]);
    }
  }
  return {
    id: variable.id,
    name: variable.name,
    collection_id: variable.variableCollectionId,
    resolved_type: variable.resolvedType,
    description: variable.description || "",
    scopes: Array.isArray(variable.scopes) ? variable.scopes.slice() : [],
    remote: !!variable.remote,
    hidden_from_publishing: !!variable.hiddenFromPublishing,
    code_syntax: Object.assign({}, variable.codeSyntax || {}),
    values_by_mode: values
  };
}

const capturedAt = new Date().toISOString();
const fileKey = figma.fileKey || null;
const allCollections = await figma.variables.getLocalVariableCollectionsAsync();
const base = {
  chunk_type: "figma_token_variables",
  chunk_version: "1.0.0",
  adapter_id: ADAPTER_ID,
  adapter_version: ADAPTER_VERSION,
  captured_at: capturedAt,
  source: { file_key: fileKey, file_name: figma.root.name }
};

if (CONFIG.mode === "inventory") {
  return Object.assign(base, {
    operation: "inventory",
    complete: true,
    collections: allCollections.map(collectionRecord)
  });
}

if (CONFIG.mode === "variables") {
  const requested = CONFIG.collectionIds.length
    ? allCollections.filter((collection) => CONFIG.collectionIds.includes(collection.id))
    : allCollections;
  const variables = [];
  const completedCollectionIds = [];
  const collectionProgress = [];
  let truncated = false;
  for (const collection of requested) {
    let collectionComplete = true;
    const start = Number.isInteger(CONFIG.startByCollection[collection.id]) ? CONFIG.startByCollection[collection.id] : 0;
    let end = start;
    for (const variableId of collection.variableIds.slice(start)) {
      if (variables.length >= CONFIG.maxVariables) {
        truncated = true;
        collectionComplete = false;
        break;
      }
      end++;
      const variable = await figma.variables.getVariableByIdAsync(variableId);
      if (!variable) {
        collectionComplete = false;
        continue;
      }
      variables.push(await variableRecord(variable, collection));
    }
    collectionComplete = collectionComplete && end >= collection.variableIds.length;
    collectionProgress.push({ collection_id: collection.id, start, end, total: collection.variableIds.length, complete: collectionComplete });
    if (collectionComplete) completedCollectionIds.push(collection.id);
    if (truncated) break;
  }
  return Object.assign(base, {
    operation: "variables",
    requested_collection_ids: requested.map((collection) => collection.id),
    completed_collection_ids: completedCollectionIds,
    collection_progress: collectionProgress,
    truncated,
    variables
  });
}

return Object.assign(base, { error: `Unsupported CONFIG.mode: ${CONFIG.mode}` });
