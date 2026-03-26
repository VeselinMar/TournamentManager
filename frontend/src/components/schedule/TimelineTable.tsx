import { useEffect, useRef } from "react";
import { Table, TableHead, TableRow, TableCell, TableBody, Paper } from "@mui/material";
import "./TimelineTable.css";

interface MatchData {
  id: number;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  is_finished: boolean;
}

interface TimelineRow {
  time: string;
  matches: (MatchData | null)[];
}

interface TimelineTableProps {
  fieldNames: string[];
  timeline: TimelineRow[];
}

export default function TimelineTable({ fieldNames, timeline }: TimelineTableProps) {
  const tableRef = useRef<HTMLTableElement>(null);

  useEffect(() => {
    if (!tableRef.current) return;

    const rowIndex = timeline.findIndex(row =>
      row.matches.some(m => m && !m.is_finished)
    );

    if (rowIndex >= 0) {
      const rowElem = tableRef.current.rows[rowIndex + 1];
      rowElem?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [timeline]);

  return (
    <Paper elevation={3} className="table-container">
      <Table ref={tableRef} className="timeline-table">
        <TableHead>
          <TableRow>
            <TableCell className="time-cell">Time</TableCell>
            {fieldNames.map(f => (
              <TableCell key={f}>{f}</TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {timeline.map((row, idx) => (
            <TableRow key={idx}>
              <TableCell className="time-cell">{row.time}</TableCell>
              {row.matches.map((match, fIdx) => (
                <TableCell key={fIdx}>
                  {match ? (
                    <div className={`match-card ${match.is_finished ? "finished" : "current"}`}>
                      <div className="teams">
                        <strong>{match.home_team}</strong> vs <strong>{match.away_team}</strong>
                      </div>
                      {match.is_finished && (
                        <div className="score">
                          {match.home_score} : {match.away_score}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="no-match">—</div>
                  )}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Paper>
  );
}