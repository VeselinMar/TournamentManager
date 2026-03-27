import "./SponsorBanner.css";

type Sponsor = {
  name: string;
  image_url: string | null;
  link_url: string;
};

interface Props {
  sponsors: Sponsor[];
  position?: "top" | "bottom";
}

export default function SponsorBanner({ sponsors, position = "top" }: Props) {
  if (!sponsors.length) {
    return (
      <div className={`sponsor-banner sponsor-${position}`}>
        <p>No sponsors yet</p>
      </div>
    );
  }

  const displaySponsors =
    position === "bottom" ? [...sponsors].reverse() : sponsors;

  return (
    <div className={`sponsor-banner sponsor-${position}`}>
      {displaySponsors.map((s) => (
        <a key={s.name} href={s.link_url} target="_blank">
          {s.image_url && (
            <img src={s.image_url} alt={s.name} />
          )}
        </a>
      ))}
    </div>
  );
}