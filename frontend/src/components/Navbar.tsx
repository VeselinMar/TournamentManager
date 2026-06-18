import { Box, IconButton } from "@mui/material";
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
    <Box
      sx={{
        position: "sticky",
        top: 0,
        zIndex: 1000,

        display: "flex",
        justifyContent: "center",
        gap: 2,

        padding: "0.4rem 0.5rem",

        background: "rgba(255, 255, 255, 0.25)",
        backdropFilter: "blur(10px)",
        WebkitBackdropFilter: "blur(10px)",

        borderBottom: "1px solid rgba(85, 107, 47, 0.25)",
      }}
    >
      {sections.map((section) => {
        const Icon = iconMap[section.path] ?? ScheduleIcon;
        const isActive = location.pathname.endsWith(section.path);

        return (
          <IconButton
            key={section.path}
            onClick={() => onSelect(section.path)}
            sx={{
              color: isActive ? "#1b5e20" : "rgba(27, 58, 0, 0.6)",

              backgroundColor: isActive
                ? "rgba(85, 107, 47, 0.12)"
                : "transparent",

              borderRadius: "8px",
              padding: "6px 10px",

              transition: "all 0.2s ease",

              "&:hover": {
                backgroundColor: "rgba(85, 107, 47, 0.08)",
                color: "#1b5e20",
              },
            }}
          >
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                lineHeight: 1,
              }}
            >
              <Icon fontSize="small" />
              <span style={{ fontSize: 11, marginTop: 2 }}>
                {section.label}
              </span>
            </Box>
          </IconButton>
        );
      })}
    </Box>
  );
}