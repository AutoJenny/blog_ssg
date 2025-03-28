// .eleventy.js
module.exports = function(eleventyConfig) {

    // --- Add this line: ---
    eleventyConfig.addCollection("post", function(collectionApi) {
      // Get all files in the 'posts' directory, sorted by filename (or date if available)
      return collectionApi.getFilteredByGlob("./posts/**/*.md");
    });
    // --- End of added line ---
  
    // Tell Eleventy to copy the 'css' and 'images' directories...
    eleventyConfig.addPassthroughCopy("css");
    eleventyConfig.addPassthroughCopy("images");
  
    // Specify input and output directories
    return {
      dir: {
        input: ".",          // Root folder for input files (includes posts, etc.)
        includes: "_includes", // Folder for layouts, partials
        output: "_site"      // Folder where the built site will go (default)
      },
      // Files read by Eleventy, add as needed
      templateFormats: ["md", "njk", "html"],
      // Use Nunjucks for Markdown files
      markdownTemplateEngine: "njk",
      // Use Nunjucks for HTML files
      htmlTemplateEngine: "njk"
    };
  };