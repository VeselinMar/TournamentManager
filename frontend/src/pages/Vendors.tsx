import { useEffect, useState } from "react";
import apiClient from "../api/client";
import type { Vendor } from "../types/vendors";

interface Props {
  slug: string;
}

export default function Vendors({ slug }: Props) {
  const [data, setData] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchVendors = async () => {
    try {
      const res = await apiClient.get<Vendor[]>(
        `/tournaments/${slug}/vendors/`
      );
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVendors();
  }, [slug]);

  if (loading) return <div>Loading vendors...</div>;
  if (!data) return <div>No vendors available</div>;

  const grouped = data.reduce((acc, vendor) => {
  if (!acc[vendor.category]) {
    acc[vendor.category] = [];
  }
  acc[vendor.category].push(vendor);
  return acc;
}, {} as Record<string, Vendor[]>);

return (
  <div>
    <h2>Vendors</h2>

    {Object.entries(grouped).map(([category, vendors]) => (
      <div key={category} style={{ marginBottom: "2rem" }}>
        <h3>{category}</h3>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
            gap: "1rem",
          }}
        >
          {vendors.map((v) => (
            <div
              key={v.id}
              style={{
                border: "1px solid #ccc",
                borderRadius: "8px",
                padding: "1rem",
                background: "#fff",
              }}
            >
              <strong>{v.name}</strong>

              {v.image_url && (
                <img
                  src={v.image_url}
                  alt={v.name}
                  style={{
                    width: "100%",
                    height: "120px",
                    objectFit: "cover",
                    marginTop: "0.5rem",
                    borderRadius: "4px",
                  }}
                />
              )}

              <div style={{ marginTop: "0.5rem", fontSize: "0.9rem" }}>
                {v.description}
              </div>
            </div>
          ))}
        </div>
      </div>
    ))}
  </div>
);
}