import { Typography, Box, Chip } from "@mui/material";

interface HeaderProps {
  name: string;
  isFinished: boolean;
  liveCount?: number;
}

export default function Header({ name, isFinished, liveCount = 0 }: HeaderProps) {
  return (
    <Box
      sx={{
        mb: 3,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 1,
      }}
    >
      {/* Title */}
      <Typography
        variant="h3"
        component="h1"
        sx={{
          fontFamily: "inherit",
          color: "#1e3d2f",
          fontWeight: 800,
          letterSpacing: "0.01em",
          textAlign: "center",
        }}
      >
        {name}
      </Typography>

      {/* Status row */}
      <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
        <Chip
          label={isFinished ? "Finished" : "Live"}
          color={isFinished ? "default" : "error"}
          size="small"
        />

        {!isFinished && liveCount > 0 && (
          <Typography variant="caption" sx={{ opacity: 0.7 }}>
            🔴 {liveCount} matches live
          </Typography>
        )}
      </Box>
    </Box>
  );
}