import React from "react";
import { Outlet } from "react-router-dom";
import InstructorSidebar from "./InstructorSidebar";

export const InstructorLayout = () => {
  return (
    <div className="flex h-screen bg-bg-glass text-text-main overflow-hidden">
      <InstructorSidebar />
      <main className="min-w-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
        <div className="max-w-6xl mx-auto w-full">
        <Outlet />
      </div>
      </main>
    </div>
  );
};

export default InstructorLayout;