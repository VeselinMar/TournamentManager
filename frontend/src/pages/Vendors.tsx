import { useEffect, useState } from "react";
import apiClient from "../api/client";
import type { Vendor } from "../types/vendors";
import { Box, Typography, Card, CardContent, Grid } from "@mui/material";
import styles from "../modules/Vendors.module.css"

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
  <Box className={styles.container}>
  {Object.entries(grouped).map(([category, vendors]) => (
    <div key={category} className={styles.category}>
      <Typography variant="h5" className={styles.categoryTitle}>
        {category}
      </Typography>

      <Grid container spacing={2}>
        {vendors.map((v) => (
          <Grid size={{ xs:12, sm:6, md:4 }} key={v.id}>
            <Card className={styles.card}>
              <CardContent>
                <Typography variant="h6">{v.name}</Typography>

                {v.image_url && (
                  <img
                    src={v.image_url}
                    alt={v.name}
                    className={styles.image}
                  />
                )}

                <Typography variant="body2">
                  {v.description}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </div>
  ))}
</Box>
);
}