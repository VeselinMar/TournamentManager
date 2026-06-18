import { Typography, Box } from "@mui/material";

interface HeaderProps {
  name: string;
  isFinished: boolean;
  liveCount?: number;
}

export default function Header({ name }: HeaderProps) {
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
    </Box>
  );
}