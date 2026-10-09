#[path = "support/emit_and_run.rs"]
mod emit_and_run;
#[test]
fn model_class_initializer_is_retained() {
 emit_and_run::empty_app()
 .write("db/schema.rb", "ActiveRecord::Schema.define do\n create_table :widgets do |t|\n  t.string :name\n end\nend\n")
 .write("app/models/application_record.rb", "class ApplicationRecord < ActiveRecord::Base\n primary_abstract_class\nend\n")
 .write("app/models/widget.rb", "class Widget < ApplicationRecord\n @calls = 0\n def self.calls\n  @calls\n end\nend\n")
 .write("app/controllers/application_controller.rb", "class ApplicationController < ActionController::API\nend\n")
 .write("config/routes.rb", "Rails.application.routes.draw do\nend\n")
 .run_ruby("raise Widget.calls.inspect unless Widget.calls == 0\n").assert_passes();
}
