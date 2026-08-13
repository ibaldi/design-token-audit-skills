# Scope Intent Heuristics

Use these heuristics as signals, not proof. Prefer evidence from type, collection, description, peer tokens, and usage over name alone.

## Common Intent Signals

Background or surface:

- name contains `background`, `bg`, `surface`, `container`, `fill`
- likely paint/fill scope

Foreground or text:

- name contains `foreground`, `fg`, `text`, `label`, `content`
- likely text paint scope; may also apply to icon fill depending on library convention

Border or stroke:

- name contains `border`, `stroke`, `outline`, `divider`
- likely stroke scope

Radius or corner:

- name contains `radius`, `corner`, `round`
- likely corner radius scope

Spacing, gap, or padding:

- name contains `space`, `spacing`, `gap`, `padding`, `inset`
- likely gap or padding-related float scopes

Sizing:

- name contains `size`, `width`, `height`, `min`, `max`
- likely width/height-related float scopes

Opacity:

- name contains `opacity`, `alpha`
- likely opacity scope or documented direct value exception

Effect or elevation:

- name contains `shadow`, `blur`, `elevation`, `effect`
- likely effect-related scope

Typography:

- name contains `typography`, `font`, `line-height`, `letter-spacing`, `paragraph`, `text-style`
- high risk; do not change automatically

## Finding Examples

Possible scope too broad:

```text
Component/Button/Background/Primary
Type: COLOR
Current scopes: ALL_SCOPES
Likely intent: button background fill
Recommendation: Review narrowing to fill-related scopes.
```

Possible scope mismatch:

```text
Component/Card/Border/Default
Type: COLOR
Current scopes: fill-only
Likely intent: border stroke
Recommendation: Review stroke scope.
```

Possible accepted exception:

```text
Sizing/Typography/LineHeight/Body
Type: FLOAT
Current scopes: ALL_SCOPES
Likely intent: typography sizing
Recommendation: Hold unless Typography scope cleanup is explicitly approved.
```

## Risk Notes

`ALL_SCOPES` is not automatically wrong. It means the token is available broadly and must be checked against intended use.

Missing or narrow scopes are not automatically wrong either. A token may be intentionally restricted.

Do not recommend a scope write when:

- intent is ambiguous
- source scan did not observe scope metadata
- external consumer usage is unknown and the change could hide a token from workflows
- Typography or AX behavior may be affected
- the token is documented as a special case
