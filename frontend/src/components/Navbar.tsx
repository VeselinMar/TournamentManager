import { Box, Tabs, Tab } from "@mui/material";
import { useState } from "react";

interface NavbarProps {
  sections: string[];
  onSelect: (section: string) => void;
}

export default function Navbar({ sections, onSelect }: NavbarProps) {
  const [active, setActive] = useState(0);

  const handleChange = (_: React.SyntheticEvent, newValue: number) => {
    setActive(newValue);
    onSelect(sections[newValue]);
  };

  return (
    <Box sx={{ width: "100%", borderBottom: 1, borderColor: "divider", mb: 2 }}>
      <Tabs
        value={active}
        onChange={handleChange}
        variant="scrollable"
        scrollButtons
        allowScrollButtonsMobile
        textColor="primary"
        indicatorColor="primary"
      >
        {sections.map((section) => (
          <Tab key={section} label={section} />
        ))}
      </Tabs>
    </Box>
  );
}