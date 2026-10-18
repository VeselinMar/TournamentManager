interface TeamNameProps {
  name: string;
  placeholder: boolean;
  isWinner?: boolean;
}

/** Team name; undecided knockout slots are shown in a lighter italic style. */
export function TeamName({ name, placeholder, isWinner = false }: TeamNameProps) {
  if (placeholder) {
    return (
      <span style={{ fontStyle: "italic", fontWeight: 500, color: "#6b6b6b" }}>
        {name}
      </span>
    );
  }
  return (
    <strong style={{ textDecoration: isWinner ? "underline" : "none" }}>
      {name}
    </strong>
  );
}
