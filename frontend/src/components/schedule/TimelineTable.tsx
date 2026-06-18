import { useEffect, useRef } from "react";

type MatchData = {
  id: number;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  is_finished: boolean;
};

type TimelineRow = {
  time: string;
  matches?: (MatchData | null)[];
};

interface TimelineTableProps {
  fieldNames?: string[];
  timeline?: TimelineRow[];
  maxHeight?: number | string;
}

export default function TimelineTable({
  fieldNames = [],
  timeline = [],
  maxHeight = "60vh",
}: TimelineTableProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const tableRef = useRef<HTMLTableElement>(null);

  useEffect(() => {
    if (!tableRef.current || timeline.length === 0) return;

    const id = window.setTimeout(() => {
      const rowIndex = timeline.findIndex((row) =>
        row.matches?.some((m) => m && !m.is_finished)
      );

      if (rowIndex >= 0) {
        tableRef.current?.rows[rowIndex + 1]?.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      }
    }, 0);

    return () => clearTimeout(id);
  }, [timeline]);

  if (!timeline.length) return <div>Loading timeline...</div>;

  return (
    <div
      ref={containerRef}
      style={{
        width: "100%",
        margin: "0 auto",
        border: "1px solid #d6e2d6",
        borderRadius: 10,
        boxShadow: "0 4px 14px rgba(0,0,0,0.08)",
        maxHeight: maxHeight,
        overflowY: "auto",
        overflowX: "auto",
        background: "#f3f7f3",
      }}
      className="timeline-scrollbar"
    >
      {/* Scrollbar styling */}
      <style>
        {`
          .timeline-scrollbar::-webkit-scrollbar {
            width: 10px;
            height: 10px;
          }
          .timeline-scrollbar::-webkit-scrollbar-thumb {
            background-color: #c8d8c8;
            border-radius: 5px;
          }
          .timeline-scrollbar::-webkit-scrollbar-track {
            background-color: #eef5ee;
          }
        `}
      </style>

      <table
        ref={tableRef}
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: "clamp(0.9rem, 1vw, 1.3rem)",
          background: "#ffffff",
          color: "#1b1b1b",
        }}
      >
        <thead>
          <tr>
            <th
              style={{
                position: "sticky",
                top: 0,
                left: 0,
                zIndex: 12,
                backgroundColor: "#1f3a1f",
                color: "#fff",
                fontWeight: 800,
                textTransform: "uppercase",
                textAlign: "center",
                padding: "10px",
                borderBottom: "2px solid #d6e2d6",
              }}
            >
              Time
            </th>

            {fieldNames.map((f) => (
              <th
                key={f}
                style={{
                  position: "sticky",
                  top: 0,
                  zIndex: 10,
                  backgroundColor: "#1f3a1f",
                  color: "#fff",
                  fontWeight: 800,
                  textAlign: "center",
                  padding: "10px",
                  borderBottom: "2px solid #d6e2d6",
                  textTransform: "uppercase",
                }}
              >
                {f}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {timeline.map((row, idx) => {
            const rowBg = idx % 2 === 0 ? "#ffffff" : "#f6f8f6";

            return (
              <tr
                key={idx}
                style={{
                  backgroundColor: rowBg,
                  transition: "background 0.2s ease",
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.backgroundColor = "#e6f2e6")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.backgroundColor = rowBg)
                }
              >
                {/* TIME COLUMN */}
                <td
                  style={{
                    position: "sticky",
                    left: 0,
                    zIndex: 5,
                    backgroundColor: "#ffffff",
                    fontWeight: 700,
                    color: "#1b1b1b",
                    borderRight: "2px solid #d6e2d6",
                    padding: "10px",
                    minWidth: 70,
                    textAlign: "center",
                  }}
                >
                  {row.time}
                </td>

                {/* MATCH CELLS */}
                {(row.matches ?? []).filter(Boolean).map((match, fIdx) => (
                  <td
                    key={fIdx}
                    style={{
                      padding: "8px",
                      textAlign: "center",
                      border: "1px solid #e6e6e6",
                      minWidth: 180,
                    }}
                  >
                    {match ? (
                      <div
                        style={{
                          background: match.is_finished
                            ? "#ffffff"
                            : "#f1f8e9",
                          border: "1px solid #e0e0e0",
                          borderRadius: 6,
                          padding: "6px",
                          boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
                          fontWeight: match.is_finished ? 500 : 700,
                        }}
                      >
                        {/* TEAMS */}
                        <div
                          style={{
                            fontSize:
                              "clamp(0.85rem, 1vw, 1.1rem)",
                            color: "#1b1b1b",
                          }}
                        >
                          <strong>{match.home_team}</strong> vs{" "}
                          <strong>{match.away_team}</strong>
                        </div>

                        {/* SCORE */}
                        {match.is_finished && (
                          <div
                            style={{
                              marginTop: 4,
                              fontWeight: 800,
                              color: "#1b5e20",
                            }}
                          >
                            {match.home_score} : {match.away_score}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div
                        style={{
                          color: "#b0b0b0",
                        }}
                      >
                        —
                      </div>
                    )}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}