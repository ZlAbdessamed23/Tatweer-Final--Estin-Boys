"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FaSearch, FaBell, FaCommentDots, FaCalendarAlt, FaUser, FaHistory } from "react-icons/fa";

interface NavProps {
  tabs: string[];
  userType: "patient" | "doctor"; // Add userType prop
}

const Nav: React.FC<NavProps> = ({ tabs, userType }) => {
  const pathname = usePathname();

  const iconMap = {
    search: <FaSearch className="w-5 h-5" />, 
    notification: <FaBell className="w-5 h-5" />, 
    chat: <FaCommentDots className="w-5 h-5" />, 
    appointments: <FaCalendarAlt className="w-5 h-5" />, 
    profile: <FaUser className="w-5 h-5" />, 
    historique: <FaHistory className="w-5 h-5" />, 
  };

  return (
    <div className="p-2 mt-auto space-y-2">
      {tabs.map((tab) => {
        // Construct the link based on userType
        const linkHref = `/pages/${userType === "patient" ? "dashPat" : "dashDoc"}/${tab}`;

        return (
          <div 
            key={tab} 
            className={`
              cursor-pointer p-2 px-4 rounded-[15px] transition-all ease-in-out duration-100 text-black 
              ${pathname === linkHref ? 'bg-blue-500 text-white' : 'hover:bg-gray-100'}
            `}
          >
            <Link 
              href={linkHref}
              className="flex items-center gap-2"
            >
              {iconMap[tab as keyof typeof iconMap]}
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </Link>
          </div>
        );
      })}
    </div>
  );
};

export default Nav;
