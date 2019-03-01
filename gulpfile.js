'use strict';

const gulp = require("gulp"),
      sass = require("gulp-sass"),
      sassLint = require('gulp-sass-lint'),
      clean = require('gulp-clean');

// set paths ...
const config = {
  scssPath: "src/scss",
  jsDestPath: "application/static/javascripts",
  destPath: "application/static/stylesheets",
  govukAssetPath: "application/static/govuk-frontend/assets",
  chromeExtDest: "extensions/chrome/popup/static"
}


// Tasks used to generate latest stylesheets
// =========================================
const cleanCSS = () =>
  gulp
    .src('application/static/stylesheets/**/*', {read: false})
    .pipe(clean());
cleanCSS.description = `Delete old stylesheets files`;

// compile scss to CSS
const compileStylesheets = () =>
  gulp
    .src( config.scssPath + '/*.scss')
	  .pipe(sass({outputStyle: 'expanded',
		  includePaths: [ 'src/scss', 'src/govuk-frontend']}))
      .on('error', sass.logError)
    .pipe(gulp.dest(config.destPath));

// check .scss files against .sass-lint.yml config
const lintSCSS = () =>
  gulp
    .src('src/scss/**/*.s+(a|c)ss')
    .pipe(sassLint({
      files: {ignore: 'src/scss/styleguide/_highlight-style.scss'},
      configFile: '.sass-lint.yml'
    }))
    .pipe(sassLint.format())
    .pipe(sassLint.failOnError());


// Tasks for copying assets to application
// ======================================
const copyVendorStylesheets = () =>
  gulp
    .src('src/stylesheets/**/*')
    .pipe(gulp.dest(config.destPath));

const copyGovukAssets = () =>
  gulp
    .src('src/govuk-frontend/assets/**/*')
    .pipe(gulp.dest(config.govukAssetPath));

const copyVendorJS = () =>
  gulp
    .src('src/js/vendor/*.js')
    .pipe(gulp.dest(`${config.jsDestPath}/vendor`));

const copyGovukJS = () =>
  gulp
    .src('src/js/govuk-frontend/*.js')
    .pipe(gulp.dest(`${config.jsDestPath}/govuk-frontend`));

const copyCompiledCSS = () =>
  gulp
    .src(`${config.destPath}/dl-frontend.css`)
    .pipe(gulp.dest(`${config.chromeExtDest}`));


// Tasks to expose to CLI
// ======================
const copyAllAssets = gulp.parallel(
  copyVendorStylesheets,
  copyGovukAssets,
  copyVendorJS,
  copyGovukJS
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
const watch = () => gulp.watch("src/scss/**/*", latestStylesheets);
watch.description = `Watch all project .scss for changes, then rebuild stylesheets.`;

// Set watch as default task
exports.default = watch;
exports.stylesheets = latestStylesheets;
exports.copyAssets = copyAllAssets;
