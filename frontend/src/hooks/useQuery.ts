/* oxlint-disable react-hooks/exhaustive-deps, react/set-state-in-effect */
import { useEffect, useState, type DependencyList } from 'react'

export function useQuery<T>(
  queryFn: () => Promise<T>,
  dependencies: DependencyList,
) {
  const [data, setData] = useState<T | undefined>()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)

    queryFn()
      .then((result) => {
        if (active) setData(result)
      })
      .catch((reason: unknown) => {
        if (!active) return
        setError(reason instanceof Error ? reason.message : 'Request failed')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  // The caller supplies the request identity, not the function reference.
  }, dependencies)

  return { data, loading, error }
}
