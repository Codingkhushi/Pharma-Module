import { useState, useEffect, useCallback } from 'react'

export function useFetch(fetchFn, deps = [], initial = null) {
  const [data, setData]       = useState(initial)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetchFn()
      setData(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }, deps) // eslint-disable-line

  useEffect(() => { fetch() }, [fetch])

  return { data, loading, error, refetch: fetch }
}