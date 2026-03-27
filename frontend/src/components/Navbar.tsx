import { Box, Tabs, Tab, useTheme, useMediaQuery } from "@mui/material";
import { useState } from "react";

interface NavbarProps {
  sections: { label: string; path: string }[];
  onSelect: (path: string) => void;
}

export default function Navbar({ sections, onSelect }: NavbarProps) {
  const [active, setActive] = useState(0);
  const theme = useTheme();

  const isSmallScreen = useMediaQuery(theme.breakpoints.down("sm"));

  const handleChange = (_: React.SyntheticEvent, newValue: number) => {
    setActive(newValue);
    onSelect(sections[newValue].path);
  };

  return (
    <Box sx={{ width: "100%", borderBottom: 1, borderColor: "divider", mb: 2 }}>
      <Tabs
        value={active}
        onChange={handleChange}
        variant={isSmallScreen ? "scrollable" : "standard"}
        centered={!isSmallScreen}
        scrollButtons={isSmallScreen ? "auto" : false}
        allowScrollButtonsMobile
        textColor="primary"
        indicatorColor="primary"
      >
        {sections.map((section) => (
          <Tab key={section.path} label={section.label} />
        ))}
      </Tabs>
    </Box>
  );
}