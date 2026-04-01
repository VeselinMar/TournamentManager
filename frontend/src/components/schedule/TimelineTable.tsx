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
  maxHeight?: number | string; //
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

    const rowIndex = timeline.findIndex((row) =>
      row.matches?.some((m) => m && !m.is_finished)
    );

    if (rowIndex >= 0) {
      const rowElem = tableRef.current.rows[rowIndex + 1]; // +1 for header
      rowElem?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [timeline]);

  if (!timeline.length) return <div>Loading timeline...</div>;

  return (
    <div
      ref={containerRef}
      style={{
        width: "100%",
        border: "2px solid #556b2f",
        borderRadius: 8,
        boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
        maxHeight: maxHeight,
        overflowY: "auto",
        overflowX: "auto",
      }}
      className="timeline-scrollbar"
    >
      <style>
        {`
          .timeline-scrollbar::-webkit-scrollbar {
            width: 10px;
            height: 10px;
          }
          .timeline-scrollbar::-webkit-scrollbar-thumb {
            background-color: #a5d6a7;
            border-radius: 5px;
          }
          .timeline-scrollbar::-webkit-scrollbar-track {
            background-color: #e8f5e9;
          }
        `}
      </style>

      <table
        ref={tableRef}
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: "clamp(0.9rem, 1vw, 1.3rem",
          background: "#8fbc8f",
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
                backgroundColor: "#556b2f",
                color: "#fff",
                fontWeight: 700,
                fontSize: "clamp(0.9rem, 1vw, 1.3rem",
                textTransform: "uppercase",
                textAlign: "center",
                padding: "8px",
                border: "2px solid #a5d6a7",
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
                  fontWeight: 700,
                  textAlign: "center",
                  padding: "8px",
                  border: "2px solid #a5d6a7",
                  backgroundColor: "#3e521e",
                  color: "#fff",
                }}
              >
                {f}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {timeline.map((row, idx) => (
            <tr
              key={idx}
              style={{
                backgroundColor:
                  idx % 2 === 0 ? "rgba(255,255,255,0.03)" : "rgba(0,0,0,0.02)",
              }}
            >
              <td
                style={{
                  position: "sticky",
                  left: 0,
                  zIndex: 5,
                  backgroundColor: "#6b8e23",
                  fontWeight: "bold",
                  fontSize: "clamp(0.9rem, 1vw, 1.3rem",
                  color: "#fff",
                  border: "2px solid rgba(0,0,0,0.15)",
                  minWidth: 64,
                  padding: "8px",
                }}
              >
                {row.time}
              </td>
              {(row.matches || []).map((match, fIdx) => (
                <td
                  key={fIdx}
                  style={{
                    padding: "8px",
                    textAlign: "center",
                    border: "2px solid rgba(0,0,0,0.15)",
                  }}
                >
                  {match ? (
                    <div
                      style={{
                        background: match.is_finished
                          ? "linear-gradient(to bottom, #8fbc8f, #6b8e23)"
                          : "linear-gradient(to bottom, #ffecb3, #ffd54f)",
                        padding: "4px",
                        borderRadius: "4px",
                        margin: "2px 0",
                        boxShadow: match.is_finished
                          ? "0 2px 6px rgba(0,0,0,0.15)"
                          : "0 2px 12px rgba(0,0,0,0.25)",
                        fontWeight: match.is_finished ? "normal" : "bold",
                      }}
                    >
                      <div
                        style={{
                          fontWeight: 500,
                          fontSize: "clamp(0.9rem, 1vw, 1.3rem",
                          color: "#1b3a00",
                          marginTop: 2,
                        }}
                      >
                        <strong>{match.home_team}</strong> vs{" "}
                        <strong>{match.away_team}</strong>
                      </div>
                      {match.is_finished && (
                        <div
                          style={{
                            fontWeight: 700,
                            fontSize: "clamp(0.9rem, 1vw, 1.3rem",
                            color: "#1b3a00",
                            marginTop: 2,
                          }}
                        >
                          {match.home_score} : {match.away_score}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div style={{ color: "rgba(0,0,0,0.2)", fontSize: "clamp(0.9rem, 1vw, 1.3rem", }}>
                      —
                    </div>
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}