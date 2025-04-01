// .eleventy.js
const { DateTime } = require("luxon"); // Require Luxon for date formatting

module.exports = function(eleventyConfig) {

  // --- Date Filters ---
  eleventyConfig.addFilter("readableDate", (dateObj, format, zone) => {
    // Formats a date object -> "October 26, 2023"
    return DateTime.fromJSDate(dateObj, { zone: zone || "utc" }).toFormat(format || "LLLL dd, yyyy");
  });

  eleventyConfig.addFilter('htmlDateString', (dateObj) => {
    // Formats a date object -> "2023-10-26"
    return DateTime.fromJSDate(dateObj, { zone: 'utc' }).toFormat('yyyy-LL-dd');
  });
  // --- End Date Filters ---

  // --- Collection based on Tags ---
  // Get all content tagged with "post"
  eleventyConfig.addCollection("post", function(collectionApi) {
    // UPDATED: Filter by tag instead of glob
    return collectionApi.getFilteredByTag("post").sort(function(a, b) {
      // Ensure descending sort by date
      return b.date - a.date;
    });
  });
  // --- End Collection ---

  // --- Passthrough Copies ---
  // Tell Eleventy to copy the 'css' and 'images' directories
  eleventyConfig.addPassthroughCopy("css");
  eleventyConfig.addPassthroughCopy("images");
  // --- End Passthrough ---

      // ---  IGNORE 'docs' ---
      eleventyConfig.ignores.add("docs/"); // Ignore markdown files in docs

  // --- Return Project Configuration ---
  return {
    dir: {
      input: ".", // Root folder for input files
      includes: "_includes", // Folder for layouts, partials
      data: "_data", // (Optional) Folder for global data files
      output: "_site" // Folder where the built site will go
    },
    // Template formats to process
    templateFormats: ["md", "njk", "html"],
    // Default template engines
    markdownTemplateEngine: "njk",
    htmlTemplateEngine: "njk"
  };
  // --- End Return ---
};