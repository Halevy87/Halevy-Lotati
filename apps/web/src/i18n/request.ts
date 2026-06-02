import { getRequestConfig } from "next-intl/server";

import messages from "../../messages/he.json";

// Hebrew-only application (PRD §0). No locale routing — one static locale.
export default getRequestConfig(async () => ({
  locale: "he",
  messages,
}));
