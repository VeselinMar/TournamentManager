import { useRef, useEffect, useState } from "react";

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
  speed = 30,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);

  const [offset, setOffset] = useState(0);
  const [direction, setDirection] = useState(
    position === "top" ? -1 : 1
  );
  const [paused, setPaused] = useState(false);

  const [dimensions, setDimensions] = useState({
    containerWidth: 0,
    trackWidth: 0,
  });

useEffect(() => {
  const measure = () => {
    if (!containerRef.current || !trackRef.current) return;

    setDimensions({
      containerWidth: containerRef.current.offsetWidth,
      trackWidth: trackRef.current.scrollWidth,
    });
  };

  const idleId = requestIdleCallback(measure);

  const resizeObserver = new ResizeObserver(() => {
    requestIdleCallback(measure);
  });

  if (containerRef.current) resizeObserver.observe(containerRef.current);
  if (trackRef.current) resizeObserver.observe(trackRef.current);

  return () => {
    cancelIdleCallback(idleId);
    resizeObserver.disconnect();
  };
}, [sponsors]);

  // ✅ Set INITIAL position correctly (runs when dimensions ready)
  useEffect(() => {
    const { containerWidth, trackWidth } = dimensions;
    if (trackWidth === 0) return;

    const maxLeft = containerWidth - trackWidth;

    if (position === "top") {
      setOffset(0);
      setDirection(-1);
    } else {
      setOffset(maxLeft);
      setDirection(1);
    }
  }, [dimensions, position]);

  useEffect(() => {
    let frame: number;
    let lastTime = performance.now();

    const animate = (time: number) => {
      if (paused) {
        frame = requestAnimationFrame(animate);
        return;
      }

      const delta = (time - lastTime) / 1000;
      lastTime = time;

      const { containerWidth, trackWidth } = dimensions;

      if (trackWidth <= containerWidth) return;

      setOffset((prev) => {
        const { containerWidth, trackWidth } = dimensions;
        const maxLeft = containerWidth - trackWidth;

        // Distance to edges
        const distanceToRight = Math.abs(prev);
        const distanceToLeft = Math.abs(prev - maxLeft);

        const edgeThreshold = 40; // px → start slowing down

        // Normalize easing (0 → 1)
        const easeRight = Math.min(distanceToRight / edgeThreshold, 1);
        const easeLeft = Math.min(distanceToLeft / edgeThreshold, 1);
        
        const smooth = (t: number) => t * t * (3 - 2 * t);

        // Pick correct easing depending on direction
        const easingFactor =
          direction === -1 ? smooth(easeRight) : smooth(easeLeft);

        // Apply easing curve (smooth)
        const easedSpeed =
          speed * (0.2 + 0.8 * easingFactor); 

        let next = prev + direction * easedSpeed * delta;

        // Bounce right edge
        if (next >= 0) {
          next = 0;
          setDirection(1 * -1);
        }

        // Bounce left edge
        if (next <= maxLeft) {
          next = maxLeft;
          setDirection(-1 * -1);
        }

        return next;
      });

      frame = requestAnimationFrame(animate);
    };

    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [direction, speed, paused, dimensions]);

  if (!sponsors || sponsors.length === 0) {
    return <div>Loading sponsors...</div>;
  }

  return (
    <div
      ref={containerRef}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      style={{
        overflow: "hidden",
        width: "100%",
        position: "relative",
        padding: "10px 0",
      }}
    >
      <div
        ref={trackRef}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "20px",
          transform: `translateX(${offset}px)`,
          willChange: "transform",
        }}
      >
        {sponsors.map((s, i) => (
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
    </div>
  );
}