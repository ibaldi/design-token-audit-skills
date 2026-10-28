// collect_figma_properties.js — token-readonly-scan 0.9.0
// READ ONLY. Run as the body of a Figma Plugin API / figma_execute call.
// Emits exact binding usages plus property traversal observations for Audit 1.5.

const CONFIG = {
  mode: "page_inventory", // "page_inventory" | "pages"
  pageIds: [], // pages mode: one or a few page IDs; [] means all
  maxNodes: 40000
};

const ADAPTER_ID = "figma-console-plugin-api";
const ADAPTER_VERSION = "0.9.0";

const SIMPLE_FIELDS = [
  "height", "width", "characters", "itemSpacing", "paddingLeft", "paddingRight",
  "paddingTop", "paddingBottom", "visible", "cornerRadius", "topLeftRadius",
  "topRightRadius", "bottomLeftRadius", "bottomRightRadius", "minWidth", "maxWidth",
  "minHeight", "maxHeight", "counterAxisSpacing", "strokeWeight", "strokeTopWeight",
  "strokeRightWeight", "strokeBottomWeight", "strokeLeftWeight", "opacity",
  "gridRowGap", "gridColumnGap"
];
const TYPOGRAPHY_FIELDS = [
  "fontFamily", "fontSize", "fontStyle", "fontWeight", "letterSpacing", "lineHeight",
  "paragraphSpacing", "paragraphIndent"
];

function aliasId(value) {
  return value && typeof value === "object" && value.id ? value.id : null;
}

function literal(value) {
  if (value === undefined || typeof value === "symbol" || typeof value === "function") return null;
  if (value && typeof value === "object" && "r" in value && "g" in value && "b" in value) {
    return { r: value.r, g: value.g, b: value.b, a: "a" in value ? value.a : 1 };
  }
  if (value && typeof value === "object") {
    try { return JSON.parse(JSON.stringify(value)); } catch (_) { return String(value); }
  }
  return value;
}

function addObservation(observations, usages, node, page, family, path, value, binding, pattern = path) {
  const variableId = aliasId(binding);
  const state = variableId ? "bound" : (typeof value === "symbol" ? "mixed_or_unsupported" : "literal");
  observations.push({
    family,
    property_path: path,
    property_pattern: pattern,
    node_id: node.id,
    node_name: node.name,
    node_type: node.type,
    page_id: page.id,
    state,
    value: variableId ? null : literal(value),
    variable_id: variableId
  });
  if (variableId) {
    usages.push({
      variable_id: variableId,
      node_id: node.id,
      page_id: page.id,
      binding_path: path,
      binding_kind: "bound_variable"
    });
  }
}

function scanNode(node, page, observations, usages) {
  const bound = node.boundVariables || {};
  for (const field of SIMPLE_FIELDS) {
    if (field in node) addObservation(observations, usages, node, page, "simple_node_fields", field, node[field], bound[field]);
  }
  for (const field of TYPOGRAPHY_FIELDS) {
    if (field in node) addObservation(observations, usages, node, page, "typography", field, node[field], bound[field]);
  }
  for (const [property, family, pathPrefix] of [
    ["fills", "paints", "fills"],
    ["strokes", "paints", "strokes"],
    ["effects", "effects", "effects"],
    ["layoutGrids", "layout_grids", "layoutGrids"]
  ]) {
    const values = node[property];
    const bindings = bound[property];
    if (!Array.isArray(values)) continue;
    for (let index = 0; index < values.length; index++) {
      const item = values[index];
      if (!item || typeof item !== "object") continue;
      const itemBindings = Array.isArray(bindings) ? bindings[index] : null;
      if (property === "fills" || property === "strokes") {
        if ("color" in item) addObservation(observations, usages, node, page, family, `${pathPrefix}[${index}].color`, item.color, item.boundVariables && item.boundVariables.color ? item.boundVariables.color : itemBindings, `${pathPrefix}[*].color`);
      } else if (property === "effects") {
        for (const field of ["radius", "color", "spread", "offsetX", "offsetY"]) {
          let value = item[field];
          if (field === "offsetX" && item.offset) value = item.offset.x;
          if (field === "offsetY" && item.offset) value = item.offset.y;
          if (value !== undefined) addObservation(observations, usages, node, page, family, `${pathPrefix}[${index}].${field}`, value, item.boundVariables && item.boundVariables[field], `${pathPrefix}[*].${field}`);
        }
      } else {
        for (const field of ["sectionSize", "count", "offset", "gutterSize"]) {
          if (field in item) addObservation(observations, usages, node, page, family, `${pathPrefix}[${index}].${field}`, item[field], item.boundVariables && item.boundVariables[field], `${pathPrefix}[*].${field}`);
        }
      }
    }
  }
  if (node.componentProperties && typeof node.componentProperties === "object") {
    for (const [name, property] of Object.entries(node.componentProperties)) {
      const propertyBinding = property && property.boundVariables ? property.boundVariables.value : null;
      addObservation(observations, usages, node, page, "component_properties", `componentProperties[${JSON.stringify(name)}]`, property ? property.value : null, propertyBinding, "componentProperties[*]");
    }
  }
  if (node.type === "TEXT" && typeof node.getStyledTextSegments === "function") {
    const segments = node.getStyledTextSegments(["fills"]);
    for (let segmentIndex = 0; segmentIndex < segments.length; segmentIndex++) {
      const fills = segments[segmentIndex].fills;
      if (!Array.isArray(fills)) continue;
      for (let fillIndex = 0; fillIndex < fills.length; fillIndex++) {
        const paint = fills[fillIndex];
        if (paint && typeof paint === "object" && "color" in paint) {
          const path = `textRangeFills[${segmentIndex}:${fillIndex}].color`;
          addObservation(observations, usages, node, page, "paints", path, paint.color, paint.boundVariables && paint.boundVariables.color, "textRangeFills[*].color");
        }
      }
    }
  }
}

async function scanPage(page, remainingBudget) {
  if (page.loadAsync) await page.loadAsync();
  const observations = [];
  const usages = [];
  let nodeCount = 0;
  let truncated = false;
  const stack = [page];
  while (stack.length) {
    const node = stack.pop();
    if (nodeCount >= remainingBudget) { truncated = true; break; }
    nodeCount++;
    if (node !== page) scanNode(node, page, observations, usages);
    if ("children" in node && Array.isArray(node.children)) {
      for (let index = node.children.length - 1; index >= 0; index--) stack.push(node.children[index]);
    }
  }
  return {
    id: page.id,
    name: page.name,
    traversal_status: truncated ? "partial" : "complete",
    node_count: nodeCount,
    observations,
    usages,
    limitations: truncated ? [`Node limit ${CONFIG.maxNodes} reached`] : []
  };
}

const base = {
  chunk_type: "figma_token_properties",
  chunk_version: "1.0.0",
  adapter_id: ADAPTER_ID,
  adapter_version: ADAPTER_VERSION,
  captured_at: new Date().toISOString(),
  source: { file_key: figma.fileKey || null, file_name: figma.root.name }
};
const pages = figma.root.children;
if (CONFIG.mode === "page_inventory") {
  return Object.assign(base, {
    operation: "page_inventory",
    complete: true,
    pages: pages.map((page) => ({ id: page.id, name: page.name }))
  });
}
if (CONFIG.mode === "pages") {
  const selected = CONFIG.pageIds.length ? pages.filter((page) => CONFIG.pageIds.includes(page.id)) : pages;
  const results = [];
  let remaining = CONFIG.maxNodes;
  for (const page of selected) {
    if (remaining <= 0) break;
    const result = await scanPage(page, remaining);
    remaining -= result.node_count;
    results.push(result);
  }
  return Object.assign(base, {
    operation: "pages",
    requested_page_ids: selected.map((page) => page.id),
    completed_page_ids: results.filter((page) => page.traversal_status === "complete").map((page) => page.id),
    pages: results
  });
}
return Object.assign(base, { error: `Unsupported CONFIG.mode: ${CONFIG.mode}` });
