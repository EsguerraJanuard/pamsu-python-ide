import { useState } from "react";
import Sidebar from "../../components/layout/Sidebar";
import Statusbar from "../../components/layout/Statusbar";

const PREVIEW_PROFILE = {

  fullName: "Student Account",

  schoolId: "0000000000",

  email: "student@pampangastateu.edu.ph",

  courseCode: "No active class",

  section: "Not assigned",

};



function getStoredProfile() {

  try {

    const storedUser = sessionStorage.getItem("user");



    if (!storedUser) {

      return PREVIEW_PROFILE;

    }



    const user = JSON.parse(storedUser);



    return {

      fullName:

        user.fullName ||

        user.full_name ||

        user.name ||

        PREVIEW_PROFILE.fullName,

      schoolId:

        user.schoolId ||

        user.school_id ||

        user.institutionalId ||

        user.institutional_id ||

        PREVIEW_PROFILE.schoolId,

      email: user.email || PREVIEW_PROFILE.email,

      courseCode:

        user.courseCode ||

        user.course_code ||

        user.course ||

        PREVIEW_PROFILE.courseCode,

      section: user.section || PREVIEW_PROFILE.section,

    };

  } catch {

    return PREVIEW_PROFILE;

  }

}



function SettingsIcon(props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
  );
}

export default function Settings() {

  const [profile, setProfile] = useState(getStoredProfile);

  const [passwords, setPasswords] = useState({

    currentPassword: "",

    newPassword: "",

    confirmPassword: "",

  });



  const [showPasswords, setShowPasswords] = useState(false);

  const [profileMessage, setProfileMessage] = useState("");

  const [passwordMessage, setPasswordMessage] = useState("");

  const [passwordMessageType, setPasswordMessageType] =

    useState("error");



  const inputWrap =

    "flex items-center gap-2.5 rounded-lg border border-border-subtle bg-bg-base px-3 py-2.5 transition-colors duration-200 focus-within:border-[#3b82f6]/60";



  const inputClass =

    "flex-1 bg-transparent text-sm text-text-main outline-none placeholder-white/20";



  const readonlyInputClass =

    "flex-1 cursor-not-allowed bg-transparent text-sm text-text-muted outline-none";



  const updateProfileName = (value) => {

    setProfile((currentProfile) => ({

      ...currentProfile,

      fullName: value,

    }));



    setProfileMessage("");

  };



  const updatePasswordField = (field, value) => {

    setPasswords((currentPasswords) => ({

      ...currentPasswords,

      [field]: value,

    }));



    setPasswordMessage("");

  };



  const handleSaveProfile = (event) => {

    event.preventDefault();



    if (profile.fullName.trim().length < 3) {

      setProfileMessage("Enter your complete name.");

      return;

    }



    /*

     * Backend integration will be added after the authenticated

     * profile API contract and centralized API client are finalized.

     *

     * Only editable profile fields should be sent.

     * Verified school ID and email must not be changed here.

     */

    setProfileMessage(

      "Profile editing is ready, but saving is not connected to the backend yet.",

    );

  };



  const handleChangePassword = (event) => {

    event.preventDefault();



    if (!passwords.currentPassword) {

      setPasswordMessageType("error");

      setPasswordMessage("Enter your current password.");

      return;

    }



    if (passwords.newPassword.length < 8) {

      setPasswordMessageType("error");

      setPasswordMessage(

        "The new password must contain at least 8 characters.",

      );

      return;

    }



    if (

      passwords.newPassword !== passwords.confirmPassword

    ) {

      setPasswordMessageType("error");

      setPasswordMessage("The new passwords do not match.");

      return;

    }



    if (

      passwords.currentPassword === passwords.newPassword

    ) {

      setPasswordMessageType("error");

      setPasswordMessage(

        "The new password must be different from the current password.",

      );

      return;

    }



    /*

     * The backend must:

     * 1. Verify the current password.

     * 2. Validate the new password.

     * 3. Hash the new password securely.

     * 4. Revoke old sessions when required.

     */

    setPasswordMessageType("info");

    setPasswordMessage(

      "Password validation is ready, but password updating is not connected to the backend yet.",

    );

  };



  return (

    <div className="flex h-screen overflow-hidden bg-bg-base text-text-main">

      <Sidebar />



      <div className="animate-page-fade flex min-w-0 flex-1 flex-col">

        <main className="settings-page flex-1 overflow-y-auto px-6 py-6 sm:px-8">
          <style>
            {`
              @keyframes settingsFadeUp {
                from {
                  opacity: 0;
                  transform: translateY(10px);
                }

                to {
                  opacity: 1;
                  transform: translateY(0);
                }
              }

              .settings-page {
                animation:
                  settingsFadeUp 450ms
                  cubic-bezier(0.25, 0.46, 0.45, 0.94)
                  both;
              }

              @media (prefers-reduced-motion: reduce) {
                .settings-page {
                  animation: none;
                }
              }
            `}
          </style>

          <div className="w-full">



            <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between border-b border-border-subtle pb-6">

              <div>

                <h1 className="text-2xl font-bold flex items-center gap-3">

                  <SettingsIcon className="h-6 w-6 text-text-muted" />

                  Settings
                </h1>
                <p className="mt-1 text-sm text-text-muted">
                  Manage your profile and account security.
                </p>
              </div>
            </header>



            <div className="space-y-6">

              <section className="rounded-xl border border-border-subtle bg-bg-glass p-5">

                <div className="mb-4">

                  <h2 className="text-sm font-semibold">

                    Profile Information

                  </h2>



                  <p className="mt-1 text-[11px] text-text-muted">

                    Verified identity details cannot be changed from

                    this page.

                  </p>

                </div>



                {profileMessage && (

                  <div

                    role="status"

                    aria-live="polite"

                    className="mb-4 rounded-lg border border-blue-500/20 bg-blue-500/10 px-4 py-3 text-sm text-blue-300"

                  >

                    {profileMessage}

                  </div>

                )}



                <form

                  onSubmit={handleSaveProfile}

                  className="space-y-4"

                >

                  <div>

                    <label

                      htmlFor="settings-full-name"

                      className="mb-1.5 block text-xs font-medium text-text-muted"

                    >

                      Complete name

                    </label>



                    <div className={inputWrap}>

                      <input

                        id="settings-full-name"

                        type="text"

                        value={profile.fullName}

                        onChange={(event) =>

                          updateProfileName(event.target.value)

                        }

                        autoComplete="name"

                        required

                        className={inputClass}

                        style={{ caretColor: "#3b82f6" }}

                      />

                    </div>

                  </div>



                  <div>

                    <label

                      htmlFor="settings-school-id"

                      className="mb-1.5 block text-xs font-medium text-text-muted"

                    >

                      School ID

                    </label>



                    <div className={`${inputWrap} opacity-70`}>

                      <input

                        id="settings-school-id"

                        type="text"

                        value={profile.schoolId}

                        disabled

                        className={readonlyInputClass}

                      />



                      <span className="shrink-0 text-[10px] text-text-muted">

                        Verified

                      </span>

                    </div>



                    <p className="mt-1.5 text-[11px] text-text-muted">

                      Contact an authorized administrator to correct

                      an invalid school ID.

                    </p>

                  </div>



                  <div>

                    <label

                      htmlFor="settings-email"

                      className="mb-1.5 block text-xs font-medium text-text-muted"

                    >

                      University email

                    </label>



                    <div className={`${inputWrap} opacity-70`}>

                      <input

                        id="settings-email"

                        type="email"

                        value={profile.email}

                        disabled

                        className={readonlyInputClass}

                      />



                      <span className="shrink-0 text-[10px] text-text-muted">

                        OTP verified

                      </span>

                    </div>



                    <p className="mt-1.5 text-[11px] text-text-muted">

                      Changing the verified email will require a

                      separate OTP verification process.

                    </p>

                  </div>



                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">

                    <div>

                      <label

                        htmlFor="settings-course"

                        className="mb-1.5 block text-xs font-medium text-text-muted"

                      >

                        Active class

                      </label>



                      <div className={`${inputWrap} opacity-70`}>

                        <input

                          id="settings-course"

                          type="text"

                          value={profile.courseCode}

                          disabled

                          className={readonlyInputClass}

                        />

                      </div>

                    </div>



                    <div>

                      <label

                        htmlFor="settings-section"

                        className="mb-1.5 block text-xs font-medium text-text-muted"

                      >

                        Section

                      </label>



                      <div className={`${inputWrap} opacity-70`}>

                        <input

                          id="settings-section"

                          type="text"

                          value={profile.section}

                          disabled

                          className={readonlyInputClass}

                        />

                      </div>

                    </div>

                  </div>



                  <div className="flex justify-end pt-1">

                    <button

                      type="submit"

                      className="rounded-lg bg-gradient-to-br from-[#3b82f6] to-[#2563eb] px-4 py-2 text-sm font-semibold text-text-main transition duration-150 hover:-translate-y-px hover:opacity-90 active:translate-y-0 active:scale-[0.98]"

                    >

                      Save profile

                    </button>

                  </div>

                </form>

              </section>



              <section className="rounded-xl border border-border-subtle bg-bg-glass p-5">

                <div className="mb-4">

                  <h2 className="text-sm font-semibold">

                    Change Password

                  </h2>



                  <p className="mt-1 text-[11px] text-text-muted">

                    Your current password must be verified by the

                    server.

                  </p>

                </div>



                {passwordMessage && (

                  <div

                    role={

                      passwordMessageType === "error"

                        ? "alert"

                        : "status"

                    }

                    aria-live="polite"

                    className={`mb-4 rounded-lg border px-4 py-3 text-sm ${

                      passwordMessageType === "error"

                        ? "border-red-500/20 bg-red-500/10 text-red-300"

                        : "border-blue-500/20 bg-blue-500/10 text-blue-300"

                    }`}

                  >

                    {passwordMessage}

                  </div>

                )}



                <form

                  onSubmit={handleChangePassword}

                  className="space-y-4"

                >

                  <div>

                    <label

                      htmlFor="current-password"

                      className="mb-1.5 block text-xs font-medium text-text-muted"

                    >

                      Current password

                    </label>



                    <div className={inputWrap}>

                      <input

                        id="current-password"

                        type={

                          showPasswords ? "text" : "password"

                        }

                        value={passwords.currentPassword}

                        onChange={(event) =>

                          updatePasswordField(

                            "currentPassword",

                            event.target.value,

                          )

                        }

                        placeholder="Enter your current password"

                        autoComplete="current-password"

                        required

                        className={inputClass}

                        style={{ caretColor: "#3b82f6" }}

                      />

                    </div>

                  </div>



                  <div>

                    <label

                      htmlFor="new-password"

                      className="mb-1.5 block text-xs font-medium text-text-muted"

                    >

                      New password

                    </label>



                    <div className={inputWrap}>

                      <input

                        id="new-password"

                        type={

                          showPasswords ? "text" : "password"

                        }

                        value={passwords.newPassword}

                        onChange={(event) =>

                          updatePasswordField(

                            "newPassword",

                            event.target.value,

                          )

                        }

                        placeholder="At least 8 characters"

                        autoComplete="new-password"

                        minLength={8}

                        required

                        className={inputClass}

                        style={{ caretColor: "#3b82f6" }}

                      />

                    </div>

                  </div>



                  <div>

                    <label

                      htmlFor="confirm-new-password"

                      className="mb-1.5 block text-xs font-medium text-text-muted"

                    >

                      Confirm new password

                    </label>



                    <div className={inputWrap}>

                      <input

                        id="confirm-new-password"

                        type={

                          showPasswords ? "text" : "password"

                        }

                        value={passwords.confirmPassword}

                        onChange={(event) =>

                          updatePasswordField(

                            "confirmPassword",

                            event.target.value,

                          )

                        }

                        placeholder="Enter the new password again"

                        autoComplete="new-password"

                        minLength={8}

                        required

                        className={inputClass}

                        style={{ caretColor: "#3b82f6" }}

                      />

                    </div>

                  </div>



                  <label className="flex cursor-pointer items-center gap-2">

                    <input

                      type="checkbox"

                      checked={showPasswords}

                      onChange={(event) =>

                        setShowPasswords(event.target.checked)

                      }

                      className="h-4 w-4 accent-[#3b82f6]"

                    />



                    <span className="text-xs text-text-muted">

                      Show passwords

                    </span>

                  </label>



                  <div className="flex justify-end pt-1">

                    <button

                      type="submit"

                      className="rounded-lg bg-gradient-to-br from-[#3b82f6] to-[#2563eb] px-4 py-2 text-sm font-semibold text-text-main transition duration-150 hover:-translate-y-px hover:opacity-90 active:translate-y-0 active:scale-[0.98]"

                    >

                      Update password

                    </button>

                  </div>

                </form>

              </section>



              <section className="rounded-xl border border-border-subtle bg-bg-glass p-5">

                <h2 className="text-sm font-semibold">

                  Privacy and Session Security

                </h2>



                <ul className="mt-3 list-inside list-disc space-y-2 text-[11px] leading-relaxed text-text-muted">

                  <li>

                    The browser-stored profile is used only for

                    interface display.

                  </li>

                  <li>

                    The backend must validate every protected request

                    using the authenticated token.

                  </li>

                  <li>

                    Passwords must never be stored or logged by the

                    frontend.

                  </li>

                  <li>

                    Signing out removes local session information from

                    this browser.

                  </li>
                </ul>
              </section>
            </div>
          </div>
        </main>

        <Statusbar />
      </div>
    </div>
);

}