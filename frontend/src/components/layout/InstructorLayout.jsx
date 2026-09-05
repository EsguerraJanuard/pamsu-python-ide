import React from "react";
import { Outlet } from "react-router-dom";
import InstructorSidebar from "./InstructorSidebar";

export const InstructorLayout = () => {
  return (
    <div className="flex h-screen bg-bg-glass text-text-main overflow-hidden">
      <InstructorSidebar />
      <main className="flex-1 overflow-y-auto p-8">
        <Outlet />
      </main>
    </div>
  );
};

export default InstructorLayout;