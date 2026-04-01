import { useRef, useEffect, useState } from "react";

type Sponsor = {
  name: string;
  image_url: string | null;
  link_url: string;
};

interface Props {
  sponsors: Sponsor[];
  position?: "top" | "bottom";
  speed?: number; // pixels per second
}

export default function SponsorCarousel({
  sponsors,
  position = "top",
  speed = 60,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const [trackWidth, setTrackWidth] = useState(0);
  const [visibleSponsors, setVisibleSponsors] = useState<Sponsor[]>([]);

  if (!sponsors || sponsors.length === 0) {
    return <div>Loading sponsors...</div>;
  }

  useEffect(() => {
    if (!containerRef.current) return;
    const containerWidth = containerRef.current.offsetWidth;

    // Temporary div to measure width
    const tempDiv = document.createElement("div");
    tempDiv.style.display = "inline-flex";
    tempDiv.style.visibility = "hidden";
    tempDiv.style.position = "absolute";
    tempDiv.style.top = "0";
    tempDiv.style.left = "0";
    document.body.appendChild(tempDiv);

    sponsors.forEach((s) => {
      const a = document.createElement("a");
      a.style.flexShrink = "0";
      a.style.marginRight = "20px";
      const img = document.createElement("img");
      img.src = s.image_url || "";
      img.alt = s.name;
      img.style.height = "60px";
      img.style.width = "auto";
      img.style.objectFit = "contain";
      a.appendChild(img);
      tempDiv.appendChild(a);
    });

    let currentSponsors = [...sponsors];
    let totalWidth = tempDiv.offsetWidth;

    // Duplicate sponsors until track is at least twice container width
    while (totalWidth < containerWidth * 2) {
      currentSponsors = [...currentSponsors, ...sponsors];
      tempDiv.innerHTML = "";
      currentSponsors.forEach((s) => {
        const a = document.createElement("a");
        a.style.flexShrink = "0";
        a.style.marginRight = "20px";
        const img = document.createElement("img");
        img.src = s.image_url || "";
        img.alt = s.name;
        img.style.height = "60px";
        img.style.width = "auto";
        img.style.objectFit = "contain";
        a.appendChild(img);
        tempDiv.appendChild(a);
      });
      totalWidth = tempDiv.offsetWidth;
      if (currentSponsors.length > sponsors.length * 20) break;
    }

    document.body.removeChild(tempDiv);
    setVisibleSponsors(currentSponsors);
    setTrackWidth(totalWidth);
  }, [sponsors]);

  const animationDuration = trackWidth / speed;

  return (
    <div
      ref={containerRef}
      style={{
        overflow: "hidden",
        width: "100%",
        position: "relative",
        marginTop: position === "top" ? 0 : undefined,
        marginBottom: position === "bottom" ? 0 : undefined,
      }}
    >
      <div
        ref={trackRef}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "20px",
          marginTop: "10px",
          marginBottom: "10px",
          animationName: "scroll",
          animationTimingFunction: "linear",
          animationIterationCount: "infinite",
          animationDuration: `${animationDuration}s`,
          whiteSpace: "nowrap",
        }}
      >
        {visibleSponsors.map((s, i) => (
          <a
            key={`sponsor-${i}`}
            href={s.link_url}
            target="_blank"
            rel="noopener noreferrer"
            title={s.name}
            style={{ flexShrink: 0 }}
          >
            {s.image_url ? (
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
            )}
          </a>
        ))}
      </div>

      {/* Inline keyframes */}
      <style>
        {`
          @keyframes scroll {
            0% { transform: translateX(0); }
            100% { transform: translateX(-50%); }
          }
        `}
      </style>
    </div>
  );
}