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
  // Eleventy automatically handles files in the input directory that match passthrough formats
  // unless they are explicitly processed by a template engine.
  // Using addPassthroughCopy ensures they are copied even if not directly referenced.
  eleventyConfig.addPassthroughCopy("css");
  eleventyConfig.addPassthroughCopy("images"); // Copies the entire images directory structure
  // --- End Passthrough ---

  // --- Ignored Files/Directories ---
  // Prevent Eleventy from trying to process Flask app files/templates or other non-site assets
  eleventyConfig.ignores.add("templates/");           // Flask templates
  eleventyConfig.ignores.add("app.py");               // Flask app
  eleventyConfig.ignores.add("post_to_clan.py");      // Python script
  eleventyConfig.ignores.add("watermark_images.py");  // Python script
  eleventyConfig.ignores.add("syndicate.py");         // Python script (if/when created)
  eleventyConfig.ignores.add("requirements.txt");     // Python dependencies
  eleventyConfig.ignores.add(".venv/");              // Python virtual environment folder
  eleventyConfig.ignores.add("README.md");            // Project README (unless you want it processed)
  eleventyConfig.ignores.add("docs/");               // Docs directory (keeping previous ignore)
  // Add any other non-Eleventy files/folders here if needed
  // --- End Ignores ---


  // --- Return Project Configuration ---
  return {
    dir: {
      input: ".", // Root folder for input files (Eleventy processes from here)
      includes: "_includes", // Folder for Eleventy layouts, partials
      data: "_data", // Folder for Eleventy global data files
      output: "_site" // Folder where the built site will go
    },
    // Template formats Eleventy should process if found in the input directory (and not ignored)
    templateFormats: ["md", "njk", "html"],
    // Default template engines for different file types
    markdownTemplateEngine: "njk", // Process Markdown files through Nunjucks (for layout wrapping)
    htmlTemplateEngine: "njk"      // Process HTML files through Nunjucks (for layout wrapping)
  };
  // --- End Return ---
};