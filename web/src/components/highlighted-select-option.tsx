import { Box, type SelectProps } from "@mantine/core";

/** Mantine `Select` shows a check icon on the active option by default; use this for a filled highlight instead. */
export const highlightedSelectOptionProps: Pick<SelectProps, "withCheckIcon" | "renderOption"> = {
  withCheckIcon: false,
  renderOption: ({ option, checked }) => (
    <Box
      component="span"
      display="block"
      w="100%"
      py={4}
      px="xs"
      style={{
        borderRadius: "var(--mantine-radius-sm)",
        ...(checked
          ? {
              /* `primary-light` is ~10% opacity in dark mode — too subtle on dropdown panels */
              backgroundColor:
                "color-mix(in srgb, var(--mantine-primary-color-filled) 44%, var(--mantine-color-body))",
              color: "var(--mantine-color-text)",
              fontWeight: 600,
            }
          : {}),
      }}
    >
      {option.label}
    </Box>
  ),
};
