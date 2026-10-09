export async function runExperiment(config) {
  const response = await fetch("/api/run", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(config),
  })

  const data = await response.json()

  if (!response.ok || !data.ok) {
    throw new Error(data.error || `Request failed: ${response.status}`)
  }

  return data
}