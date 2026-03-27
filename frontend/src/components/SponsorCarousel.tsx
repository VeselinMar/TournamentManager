import { useRef, useEffect, useState } from "react";
import "./SponsorCarousel.css";

type Sponsor = {
  name: string;
  image_url: string | null;
  link_url: string;
};

interface Props {
  sponsors: Sponsor[];
  position?: "top" | "bottom";
  speed?: number;
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

  useEffect(() => {
    if (!containerRef.current) return;
    const containerWidth = containerRef.current.offsetWidth;

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

    while (totalWidth < containerWidth * 2) {
      currentSponsors = [...currentSponsors, ...sponsors];
      tempDiv.innerHTML = "";
      currentSponsors.forEach((s) => {
        const a = document.createElement("a");
        a.style.flexShrink = "0";
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

  if (!sponsors.length) return null;

  const animationDuration = trackWidth / speed;

  return (
    <div
      className={`sponsor-carousel sponsor-${position}`}
      ref={containerRef}
    >
      <div
        className="sponsor-track"
        ref={trackRef}
        style={{
          animationDuration: `${animationDuration}s`,
        }}
      >
        {visibleSponsors.map((s, i) => (
          <a
            key={`sponsor-${i}`}
            href={s.link_url}
            target="_blank"
            rel="noopener noreferrer"
            title={s.name}
          >
            {s.image_url ? (
              <img src={s.image_url} alt={s.name} />
            ) : (
              <span>{s.name}</span>
            )}
          </a>
        ))}
      </div>
    </div>
  );
}