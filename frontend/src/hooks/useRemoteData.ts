import { DependencyList, useEffect, useState } from "react";

type AsyncState<T> = {
  data: T | null;
  error: string | null;
  loading: boolean;
};

export function useRemoteData<T>(loader: () => Promise<T>, deps: DependencyList) {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    error: null,
    loading: true,
  });
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setState((current) => ({ ...current, loading: true, error: null }));

    loader()
      .then((data) => {
        if (cancelled) {
          return;
        }
        setState({ data, error: null, loading: false });
      })
      .catch((error: Error) => {
        if (cancelled) {
          return;
        }
        setState({ data: null, error: error.message, loading: false });
      });

    return () => {
      cancelled = true;
    };
  }, [...deps, revision]);

  return {
    ...state,
    reload: () => setRevision((value) => value + 1),
  };
}
