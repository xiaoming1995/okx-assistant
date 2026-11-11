import { createTheme, type MantineColorsTuple } from "@mantine/core";

const workspace: MantineColorsTuple = [
  "#f3f7fa",
  "#e7edf2",
  "#d5e0e8",
  "#bdcdda",
  "#9eb3c3",
  "#7c96aa",
  "#5f788d",
  "#445e72",
  "#2d4659",
  "#172c3b"
];

export const mantineTheme = createTheme({
  primaryColor: "workspace",
  primaryShade: 8,
  colors: { workspace },
  fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  fontFamilyMonospace: '"SFMono-Regular", Consolas, "Liberation Mono", monospace',
  defaultRadius: "sm",
  radius: { xs: "4px", sm: "8px", md: "8px", lg: "12px", xl: "16px" },
  spacing: { xs: "4px", sm: "8px", md: "12px", lg: "16px", xl: "24px" },
  fontSizes: { xs: "12px", sm: "13px", md: "14px", lg: "16px", xl: "20px" },
  headings: {
    fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    fontWeight: "750"
  },
  breakpoints: { xs: "36em", sm: "48em", md: "75em", lg: "90em", xl: "120em" },
  focusRing: "auto",
  cursorType: "pointer",
  respectReducedMotion: true,
  components: {
    Button: {
      defaultProps: { radius: "sm", size: "sm" }
    },
    ActionIcon: {
      defaultProps: { radius: "sm", size: "sm", variant: "subtle" }
    },
    TextInput: {
      defaultProps: { radius: "sm", size: "sm" }
    },
    Select: {
      defaultProps: { radius: "sm", size: "sm" }
    },
    Tabs: {
      defaultProps: { variant: "pills", radius: "sm" }
    },
    Badge: {
      defaultProps: { radius: "xl", variant: "light", size: "sm" }
    },
    Alert: {
      defaultProps: { radius: "sm", variant: "light" }
    },
    Paper: {
      defaultProps: { radius: "sm", withBorder: true, shadow: "xs" }
    },
    Menu: {
      defaultProps: { shadow: "md", radius: "sm", width: 180 }
    },
    Popover: {
      defaultProps: { shadow: "md", radius: "sm" }
    },
    Modal: {
      defaultProps: { radius: "sm", overlayProps: { backgroundOpacity: 0.2, blur: 1 } }
    },
    Drawer: {
      defaultProps: { radius: "sm", overlayProps: { backgroundOpacity: 0.2, blur: 1 } }
    },
    Skeleton: {
      defaultProps: { radius: "sm", animate: true }
    },
    Table: {
      defaultProps: { highlightOnHover: true, withTableBorder: false, withColumnBorders: false }
    }
  }
});
