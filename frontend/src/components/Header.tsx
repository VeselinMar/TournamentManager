import { Typography, Box } from "@mui/material";

interface HeaderProps {
  name: string;
  isFinished: boolean;
}

export default function Header({ name }: HeaderProps) {
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
    </Box>
  );
}