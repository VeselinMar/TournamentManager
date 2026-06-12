import { Box, IconButton, Tooltip } from "@mui/material";
import ScheduleIcon from "@mui/icons-material/Schedule";
import LeaderboardIcon from "@mui/icons-material/Leaderboard";
import StoreIcon from "@mui/icons-material/Store";
import EventIcon from "@mui/icons-material/Event";
import type { SvgIconComponent } from "@mui/icons-material";
import { useLocation } from "react-router-dom";

interface Section {
  label: string;
  path: string;
}

interface NavbarProps {
  sections: Section[];
  onSelect: (path: string) => void;
}

const iconMap: Record<string, SvgIconComponent> = {
  schedule: ScheduleIcon,
  leaderboard: LeaderboardIcon,
  vendors: StoreIcon,
  "side-events": EventIcon,
};

export default function Navbar({ sections, onSelect }: NavbarProps) {
  const location = useLocation();

  return (
    <>
      <Box
        sx={{
          position: "sticky",
          top: 0,
          zIndex: 1000,
          display: "flex",
          justifyContent: "center",
          gap: 2,
          padding: "0.5rem",
          background: "rgba(255,255,255,0.9)",
        }}
      >
        {sections.map((section) => {
          const Icon = iconMap[section.path] ?? ScheduleIcon;
          const isActive = location.pathname.endsWith(section.path);

          return (
            <Tooltip title={section.label} placement="left" key={section.path}>
              <IconButton
                onClick={() => onSelect(section.path)}
                sx={{
                  color: isActive ? "#1b5e20" : "rgba(46,125,50,0.7)",
                  backgroundColor: isActive ? "#c8e6c9" : "transparent",
                  borderBottom: isActive ? "2px solid #1b5e20" : "2px solid transparent",
                  fontWeight: isActive ? 600 : 400,
                  transition: "all 0.2s ease",
                  "&:hover": {
                    backgroundColor: "#e8f5e9",
                    color: "#1b5e20",
                  },
                }}
              >
                <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                  <Icon fontSize="small" />
                  <span style={{ fontSize: 12 }}>{section.label}</span>
                </Box>

              </IconButton>
            </Tooltip>
          );
        })}
      </Box>      
    </>
  );
}