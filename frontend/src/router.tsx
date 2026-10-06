import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "@/components/layout/AppLayout";
import { ChatPage } from "@/pages/ChatPage";
import { DocumentsPage } from "@/pages/DocumentsPage";
import { EvalPage } from "@/pages/EvalPage";

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: "/", element: <ChatPage /> },
      { path: "/documentos", element: <DocumentsPage /> },
      { path: "/evaluacion", element: <EvalPage /> },
    ],
  },
]);
