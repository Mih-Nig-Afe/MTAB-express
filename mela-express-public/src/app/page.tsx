import { redirect } from "next/navigation";

// Root → redirect users to the tracking input page
export default function HomePage() {
  redirect("/track/enter");
}
