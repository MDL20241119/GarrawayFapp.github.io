const INSTAGRAM_FEED =
  "https://mdl20241119.github.io/GarrawayFapp.github.io/data/instagram.json";
const FACEBOOK_FEED =
  "https://mdl20241119.github.io/GarrawayFapp.github.io/data/facebook-events.json";

const VERIFIED_EVENT_LINKS: Record<string, string> = {
  "2026-09-05": "https://fb.me/e/7m9jmHash",
  "2026-08-18": "https://fb.me/e/4a0XAGpOz",
  "2026-08-08": "https://fb.me/e/94pcUtb5A",
};

async function fetchJson(url: string, signal?: AbortSignal) {
  const response = await fetch(url, { signal, cache: "no-store" });
  if (!response.ok) throw new Error(`Social feed responded ${response.status}`);
  return response.json();
}

export async function loadSocialData(signal?: AbortSignal) {
  const [instagramResult, facebookResult] = await Promise.allSettled([
    fetchJson(INSTAGRAM_FEED, signal),
    fetchJson(FACEBOOK_FEED, signal),
  ]);

  const instagram =
    instagramResult.status === "fulfilled" ? instagramResult.value : { posts: [] };
  const facebook =
    facebookResult.status === "fulfilled" ? facebookResult.value : { events: [] };

  return {
    instagram: {
      ...instagram,
      posts: Array.isArray(instagram?.posts)
        ? instagram.posts.map((post: Record<string, unknown>) => ({
            ...post,
            media_url: post.media_url || post.image || post.thumbnail_url,
          }))
        : [],
    },
    facebook: {
      ...facebook,
      events: Array.isArray(facebook?.events)
        ? facebook.events.map((event: Record<string, unknown>) => {
            const date = typeof event.date === "string" ? event.date : "";
            return {
              ...event,
              url: VERIFIED_EVENT_LINKS[date] || event.url,
            };
          })
        : [],
    },
  };
}
