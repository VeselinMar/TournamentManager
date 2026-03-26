import { Typography, Chip, Box } from "@mui/material";

interface HeaderProps {
  name: string;
  isFinished: boolean;
}

export default function Header({ name, isFinished }: HeaderProps) {
  return (
    <Box
      sx={{
        mb: 4,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 1.5,
      }}
    >
      <Typography
        variant="h3"
        component="h1"
        sx={{
          color: "#1e3d2f",
          fontWeight: "bold",
          letterSpacing: "0.03em",
          textAlign: "center",
        }}
      >
        {name}
      </Typography>

      <Chip
        label={isFinished ? "Finished" : "Live"}
        sx={{
          fontWeight: "bold",
          color: "#fff",
          backgroundColor: isFinished ? "#4a6351" : "#73a46c",
          borderRadius: "8px",
          px: 2,
          py: 0.6,
          cursor: isFinished ? "default" : "pointer",
          transition: "transform 0.15s ease, box-shadow 0.15s ease",
          "&:hover": {
            transform: isFinished ? "none" : "scale(1.05)",
            boxShadow: isFinished
              ? "none"
              : "0 4px 12px rgba(115, 164, 108, 0.45",
          },
          "& .MuiChip-label": {
            fontSize: "0.9rem",
          },
        }}
      />
    </Box>
  );
}