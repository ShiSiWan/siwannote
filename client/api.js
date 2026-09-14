import * as constants from "./constants.js";

import { Note, SearchResult } from "./classes.js";

import axios from "axios";
import { getStoredToken } from "./tokenStorage.js";
import { getToastOptions } from "./helpers.js";
import router from "./router.js";

const api = axios.create();

api.interceptors.request.use(
  // If the request is not for the token endpoint, add the token to the headers.
  function (config) {
    if (config.url !== "api/token") {
      const token = getStoredToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  function (error) {
    return Promise.reject(error);
  },
);

export function apiErrorHandler(error, toast) {
  if (error.response?.status === 401) {
    const redirectPath = router.currentRoute.value.fullPath;
    router.push({
      name: "login",
      query: { [constants.params.redirect]: redirectPath },
    });
  } else {
    console.error(error);
    toast.add(
      getToastOptions(
        "Unknown error communicating with the server. Please try again.",
        "Unknown Error",
        "error",
      ),
    );
  }
}

export async function getConfig() {
  try {
    const response = await api.get("api/config");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getToken(username, password, totp) {
  try {
    const response = await api.post("api/token", {
      username: username,
      password: totp ? password + totp : password,
    });
    return response.data.access_token;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function authCheck() {
  try {
    const response = await api.get("api/auth-check");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getNotes(term, sort, order, limit) {
  try {
    const response = await api.get("api/search", {
      params: {
        term: term,
        sort: sort,
        order: order,
        limit: limit,
      },
    });
    return response.data.map((note) => new SearchResult(note));
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function createNote(title, content) {
  try {
    const response = await api.post("api/notes", {
      title: title,
      content: content,
    });
    return new Note(response.data);
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getNote(title) {
  try {
    const response = await api.get(`api/notes/${encodeURIComponent(title)}`);
    return new Note(response.data);
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function updateNote(title, newTitle, newContent) {
  try {
    const response = await api.patch(`api/notes/${encodeURIComponent(title)}`, {
      newTitle: newTitle,
      newContent: newContent,
    });
    return new Note(response.data);
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function deleteNote(title) {
  try {
    await api.delete(`api/notes/${encodeURIComponent(title)}`);
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getTags() {
  try {
    const response = await api.get("api/tags");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function createAttachment(file) {
  try {
    const formData = new FormData();
    formData.append("file", file);
    const response = await api.post("api/attachments", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

// AI API Methods
export async function getAiConfig() {
  try {
    const response = await api.get("api/ai/config");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function updateAiConfig(configData) {
  try {
    const response = await api.post("api/ai/config", configData);
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function summarizeDocument(title, content) {
  try {
    const response = await api.post("api/ai/summarize", {
      title: title,
      content: content,
    });
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function chatWithAi(docTitle, docContext, messages) {
  try {
    const response = await api.post("api/ai/chat", {
      doc_title: docTitle,
      doc_context: docContext,
      messages: messages,
    });
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getAiRawJson() {
  try {
    const response = await api.get("api/ai/raw-json");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function updateAiRawJson(jsonStr) {
  try {
    const response = await api.post("api/ai/raw-json", { json_str: jsonStr });
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function testAiConnection() {
  try {
    const response = await api.post("api/ai/test");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

// Security & Comment API Methods
export async function loginAdmin(username, password, rememberMe = false) {
  try {
    const response = await api.post("api/security/login", {
      username,
      password,
      remember_me: rememberMe,
    });
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getSecurityStatus() {
  try {
    const response = await api.get("api/security/status");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getPublicNotes() {
  try {
    const response = await api.get("api/security/public-notes");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function updatePublicNotes(notesList, allPublic = false) {
  try {
    const response = await api.post("api/security/public-notes", {
      public_notes: notesList,
      all_public: allPublic,
    });
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getComments(title) {
  try {
    const response = await api.get(`api/security/comments/${encodeURIComponent(title)}`);
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function postComment(title, author, content) {
  try {
    const response = await api.post(`api/security/comments/${encodeURIComponent(title)}`, {
      author,
      content,
    });
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function deleteComment(title, commentId) {
  try {
    const response = await api.delete(`api/security/comments/${encodeURIComponent(title)}/${commentId}`);
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getIpStats() {
  try {
    const response = await api.get("api/security/ip-stats");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function toggleIpBlacklist(ip, blacklist) {
  try {
    const response = await api.post("api/security/blacklist", {
      ip,
      action: blacklist ? "add" : "remove",
    });
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

// Password & Storage Management APIs
export async function changeAdminPassword(oldPassword, newPassword) {
  try {
    const response = await api.post("api/security/change-password", {
      old_password: oldPassword,
      new_password: newPassword,
    });
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getStorageInfo() {
  try {
    const response = await api.get("api/system/storage");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function setStoragePath(newPath, createIfMissing = true, copyExistingNotes = false) {
  try {
    const response = await api.post("api/system/storage", {
      new_path: newPath,
      create_if_missing: createIfMissing,
      copy_existing_notes: copyExistingNotes,
    });
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function syncStorageIndex() {
  try {
    const response = await api.post("api/system/sync");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function browseDirectory(path = "") {
  try {
    const response = await api.get("api/system/browse", {
      params: { path },
    });
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function getSiteConfig() {
  try {
    const response = await api.get("api/system/site-config");
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}

export async function updateSiteConfig(siteTitle, siteSubtitle) {
  try {
    const response = await api.post("api/system/site-config", {
      site_title: siteTitle,
      site_subtitle: siteSubtitle,
    });
    return response.data;
  } catch (response) {
    return Promise.reject(response);
  }
}




