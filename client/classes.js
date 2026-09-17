import router from "./router.js";

class Note {
  constructor(note) {
    this.title = note?.title;
    this.lastModified = note?.lastModified ?? note?.last_modified;
    this.last_modified = this.lastModified;
    this.content = note?.content;
    this.created = note?.created;
    this.updated = note?.updated;
    this.reviewed = note?.reviewed;
    if (note && typeof note === "object") {
      Object.assign(this, note);
    }
  }

  get lastModifiedAsDate() {
    if (!this.lastModified) return new Date();
    if (typeof this.lastModified === "number") {
      return new Date(this.lastModified * 1000);
    }
    return new Date(this.lastModified);
  }

  get lastModifiedAsString() {
    return this.lastModifiedAsDate.toLocaleString();
  }
}

class SearchResult extends Note {
  constructor(searchResult) {
    super(searchResult);
    this.score = searchResult?.score;
    this.titleHighlights = searchResult?.titleHighlights;
    this.contentHighlights = searchResult?.contentHighlights;
    this.tagMatches = searchResult?.tagMatches;
    this.created = searchResult?.created;
    this.updated = searchResult?.updated;
    this.reviewed = searchResult?.reviewed;
    if (searchResult && typeof searchResult === "object") {
      Object.assign(this, searchResult);
    }
  }

  get titleHighlightsOrTitle() {
    return this.titleHighlights ? this.titleHighlights : this.title;
  }

  get includesHighlights() {
    if (
      this.titleHighlights ||
      this.contentHighlights ||
      (this.tagMatches != null && this.tagMatches.length)
    ) {
      return true;
    } else {
      return false;
    }
  }
}

export { Note, SearchResult };

