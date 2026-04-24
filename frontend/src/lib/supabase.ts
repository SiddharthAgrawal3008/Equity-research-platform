import { createClient } from "@supabase/supabase-js";

export const supabase = createClient(
  "https://sikdswngmpejvsboriyb.supabase.co",
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNpa2Rzd25nbXBlanZzYm9yaXliIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY5NzYwNzUsImV4cCI6MjA5MjU1MjA3NX0.I1WikcvOZi_5RNAWIDosKWvP0OKV0dvg_tcMasTa1ew"
);
