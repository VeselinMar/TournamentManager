import { Box, IconButton, Tooltip, Menu, MenuItem } from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import ScheduleIcon from "@mui/icons-material/Schedule";
import LeaderboardIcon from "@mui/icons-material/Leaderboard";
import StoreIcon from "@mui/icons-material/Store";
import EventIcon from "@mui/icons-material/Event";
import type { SvgIconComponent } from "@mui/icons-material";
import { useState } from "react";
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
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const location = useLocation();

  const openMenu = (event: React.MouseEvent<HTMLElement>) => setAnchorEl(event.currentTarget);
  const closeMenu = () => setAnchorEl(null);

  return (
    <>
      {/* Desktop Vertical Sidebar */}
      <Box
        sx={{
          position: "fixed",
          right: 16,
          top: "50%",
          transform: "translateY(-50%)",
          display: { xs: "none", md: "flex" },
          flexDirection: "column",
          gap: 1,
          zIndex: 1000,
          background: "rgba(255,255,255,0.5)",
          backdropFilter: "blur(6px)",
          borderRadius: "14px",
          padding: "0.4rem",
          boxShadow: "0 4px 16px rgba(0,0,0,0.08)",
          transition: "all 0.2s ease",
          "&:hover": {
            background: "rgba(255,255,255,0.85)",
            boxShadow: "0 6px 24px rgba(0,0,0,0.15)",
          },
        }}
      >
        {sections.map((section) => {
          const Icon = iconMap[section.path] ?? ScheduleIcon;
          const isActive = location.pathname.includes(section.path);

          return (
            <Tooltip title={section.label} placement="left" key={section.path}>
              <IconButton
                onClick={() => onSelect(section.path)}
                sx={{
                  color: isActive ? "#1b5e20" : "rgba(46,125,50,0.7)",
                  backgroundColor: isActive ? "#c8e6c9" : "transparent",
                  transition: "all 0.2s ease",
                  "&:hover": {
                    backgroundColor: "#e8f5e9",
                    color: "#1b5e20",
                    transform: "scale(1.1)",
                  },
                }}
              >
                <Icon fontSize="small" />
              </IconButton>
            </Tooltip>
          );
        })}
      </Box>

      {/* Mobile Top-Right Hamburger Menu */}
      <Box
        sx={{
          position: "fixed",
          top: 16,
          right: 16,
          display: { xs: "block", md: "none" },
          zIndex: 1000,
        }}
      >
        <IconButton
          onClick={openMenu}
          sx={{
            background: "rgba(255,255,255,0.9)",
            backdropFilter: "blur(8px)",
            boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
          }}
        >
          <MenuIcon />
        </IconButton>

        <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={closeMenu}>
          {sections.map((section) => (
            <MenuItem
              key={section.path}
              onClick={() => {
                onSelect(section.path);
                closeMenu();
              }}
              selected={location.pathname.includes(section.path)}
            >
              {section.label}
            </MenuItem>
          ))}
        </Menu>
      </Box>
    </>
  );
}