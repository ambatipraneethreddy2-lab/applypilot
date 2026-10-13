import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import "./index.css";
import { getToken } from "./api";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Board from "./pages/Board";
import AddJob from "./pages/AddJob";
import JobDetail from "./pages/JobDetail";
import ResumePage from "./pages/ResumePage";
import Dashboard from "./pages/Dashboard";

function Protected({ children }) {
  return getToken() ? children : <Navigate to="/login" replace />;
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          element={
            <Protected>
              <Layout />
            </Protected>
          }
        >
          <Route path="/" element={<Board />} />
          <Route path="/add" element={<AddJob />} />
          <Route path="/jobs/:id" element={<JobDetail />} />
          <Route path="/resume" element={<ResumePage />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
