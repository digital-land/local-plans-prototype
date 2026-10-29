'use strict';

const gulp = require("gulp"),
      fs = require("fs/promises"),
      sass = require("gulp-sass")(require("sass"));

// set paths ...
const config = {
  scssPath: "src/scss",
  jsDestPath: "application/static/javascripts",
  destPath: "application/static/stylesheets",
  govukAssetPath: "application/static/govuk-frontend/assets",
  chromeExtStaticDest: "extensions/chrome/popup/static"
}


// Tasks used to generate latest stylesheets
// =========================================
const cleanCSS = () =>
  Promise.all([
    fs.rm(`${config.destPath}/dl-frontend.css`, { force: true }),
    fs.rm(`${config.destPath}/popup.css`, { force: true })
  ]);
cleanCSS.description = `Delete old compiled stylesheets`;

// compile scss to CSS
const compileStylesheets = () =>
  gulp
    .src(config.scssPath + '/*.scss')
    .pipe(sass({
      style: 'expanded',
      loadPaths: ['src/scss', 'src/govuk-frontend'],
      // govuk-frontend 2.x predates the modern Sass module system
      quietDeps: true,
      silenceDeprecations: ['import', 'global-builtin', 'slash-div', 'color-functions']
    }).on('error', sass.logError))
    .pipe(gulp.dest(config.destPath));


// Tasks for copying assets to application
// ======================================
// encoding: false stops gulp 5 corrupting binary files (fonts, images)
const copyVendorStylesheets = () =>
  gulp
    .src('src/stylesheets/**/*', { encoding: false })
    .pipe(gulp.dest(config.destPath));

const copyGovukAssets = () =>
  gulp
    .src('src/govuk-frontend/assets/**/*', { encoding: false })
    .pipe(gulp.dest(config.govukAssetPath));

const copyJS = () =>
  gulp
    .src('src/js/**/*.js')
    .pipe(gulp.dest(`${config.jsDestPath}`));

const copyCompiledCSS = () =>
  gulp
    .src([`${config.destPath}/dl-frontend.css`, `${config.destPath}/popup.css`])
    .pipe(gulp.dest(`${config.chromeExtStaticDest}`));


// Tasks to expose to CLI
// ======================
const copyAllAssets = gulp.parallel(
  copyVendorStylesheets,
  copyGovukAssets,
  copyJS
);
copyAllAssets.description = `Copy all vendor and 3rd party assets to application`;

const latestStylesheets = gulp.series(
  cleanCSS,
  compileStylesheets,
  gulp.parallel(
    copyVendorStylesheets,
    copyGovukAssets,
    copyCompiledCSS
  )
);
latestStylesheets.description = `Generate the latest stylesheets`;

// Watch for scss changes
const watch = () => {
  gulp.watch("src/scss/**/*", latestStylesheets);
  gulp.watch("src/js/**/*", copyJS);
};
watch.description = `Watch all project .scss for changes, then rebuild stylesheets.`;

// Set watch as default task
exports.default = watch;
exports.stylesheets = latestStylesheets;
exports.copyAssets = copyAllAssets;
