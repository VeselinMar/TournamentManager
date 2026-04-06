import { useMemo } from "react";

type Sponsor = {
  name: string;
  image_url: string | null;
  link_url: string | null;
};

interface Props {
  sponsors: Sponsor[];
  speed?: number; // seconds for full loop
  direction?: "left" | "right";
}

export default function SponsorCarousel({
  sponsors,
  speed = 60,
  direction = "left",
}: Props) {
  const extendedSponsors = useMemo(() => {
    if (!sponsors || sponsors.length === 0) return [];

    let result = [...sponsors];

    while (result.length < 20) {
      result = [...result, ...sponsors];
    }

    return result;
  }, [sponsors]);

  if (!extendedSponsors.length) {
    return <div>Loading sponsors...</div>;
  }

  // 🎯 If only one unique sponsor → center instead of animate
  if (sponsors.length === 1) {
    const s = sponsors[0];

    const content = s.image_url ? (
      <img
        src={s.image_url}
        alt={s.name}
        style={{
          height: "60px",
          width: "auto",
          objectFit: "contain",
        }}
      />
    ) : (
      <span>{s.name}</span>
    );

    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          padding: "10px 0",
        }}
      >
        {s.link_url ? (
          <a
            href={s.link_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            {content}
          </a>
        ) : (
          content
        )}
      </div>
    );
  }

  return (
    <div
      style={{
        overflow: "hidden",
        width: "100%",
        position: "relative",
        padding: "10px 0",
        // subtle edge fade
        maskImage:
          "linear-gradient(to right, transparent, black 10%, black 90%, transparent)",
        WebkitMaskImage:
          "linear-gradient(to right, transparent, black 10%, black 90%, transparent)",
      }}
    >
      <div
        className="carousel-track"
        style={{
          display: "flex",
          alignItems: "center",
          gap: "20px",
          width: "max-content",
          animation: `scroll ${speed}s linear infinite`,
          animationDirection: direction === "left" ? "normal" : "reverse",
        }}
      >
        {/* duplicate for seamless looping */}
        {[...extendedSponsors, ...extendedSponsors].map((s, i) => {
          const content = s.image_url ? (
            <img
              src={s.image_url}
              alt={s.name}
              loading="lazy"
              style={{
                height: "60px",
                width: "auto",
                objectFit: "contain",
              }}
            />
          ) : (
            <span>{s.name}</span>
          );

          return s.link_url ? (
            <a
              key={`${s.name}-${i}`}
              href={s.link_url}
              target="_blank"
              rel="noopener noreferrer"
              title={s.name}
              style={{ flexShrink: 0 }}
            >
              {content}
            </a>
          ) : (
            <div key={`${s.name}-${i}`} style={{ flexShrink: 0 }}>
              {content}
            </div>
          );
        })}
      </div>

      {/* 🎬 animation + interaction styles */}
      <style>
        {`
          @keyframes scroll {
            from {
              transform: translateX(0);
            }
            to {
              transform: translateX(-50%);
            }
          }

          /* pause on hover (desktop) */
          .carousel-track:hover {
            animation-play-state: paused;
          }

          /* pause on touch (mobile) */
          .carousel-track:active {
            animation-play-state: paused;
          }
        `}
      </style>
    </div>
  );
}