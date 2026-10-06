import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type DocumentOut } from "@/lib/api";

export function useDocuments() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ["documents"],
    queryFn: api.listDocuments,
    // Mientras haya algún documento en "processing", refresca cada 2s.
    refetchInterval: (q) => {
      const data = q.state.data as DocumentOut[] | undefined;
      return data?.some((d) => d.status === "processing") ? 2000 : false;
    },
    // Sigue haciendo polling aunque la pestaña no esté enfocada.
    refetchIntervalInBackground: true,
  });

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ["documents"] });

  const upload = useMutation({
    mutationFn: (file: File) => api.uploadDocument(file),
    onSuccess: invalidate,
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.deleteDocument(id),
    onSuccess: invalidate,
  });

  return { query, upload, remove };
}
