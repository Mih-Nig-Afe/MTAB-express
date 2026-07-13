// TODO: implement public tracking page (Task 27.2)
// Server-side fetch GET /api/parcels/track/{code}
// No auth required.
export default function TrackPage({ params }: { params: { code: string } }) {
  return <div>Tracking {params.code} — TODO</div>;
}
