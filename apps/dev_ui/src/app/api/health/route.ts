export async function GET() {
  return Response.json({
    status: "ok",
    service: "dev_ui",
    time: new Date().toISOString(),
  });
}
