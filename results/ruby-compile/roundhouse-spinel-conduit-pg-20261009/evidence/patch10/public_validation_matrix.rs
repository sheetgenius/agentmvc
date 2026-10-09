//! Fresh, generic Rails examples for patch 10's retained validator-message hunks.
#[path = "support/emit_and_run.rs"]
mod emit_and_run;
fn example(validation: &str, columns: &str) -> emit_and_run::Overlay {
    let schema=format!("ActiveRecord::Schema.define do\n create_table :widgets do |t|\n{columns}\n end\n create_table :owners do |t|\n  t.string :name\n end\nend\n");
    let model=format!("class Widget < ApplicationRecord\n{validation}\n def problems\n  errors.to_hash\n end\nend\n");
    emit_and_run::empty_app()
        .write("db/schema.rb", &schema)
        .write("app/models/application_record.rb", "class ApplicationRecord < ActiveRecord::Base\n primary_abstract_class\nend\n")
        .write("app/models/widget.rb", &model)
        .write("app/models/owner.rb", "class Owner < ApplicationRecord\nend\n")
        .write("app/controllers/application_controller.rb", "class ApplicationController < ActionController::API\nend\n")
        .write("config/routes.rb", "Rails.application.routes.draw do\nend\n")
}
#[test]
fn presence_retains_attribute_and_short_message() {
 example(" validates :name, presence: true", " t.string :name").run_ruby("w=Widget.new(name: '')\nw.valid?\nraise w.problems.inspect unless w.problems[:name] == [\"can't be blank\"]\n").assert_passes();
}
#[test]
fn absence_retains_attribute_and_short_message() {
 example(" validates :name, absence: true", " t.string :name").run_ruby("w=Widget.new(name: 'set')\nw.valid?\nraise w.problems.inspect unless w.problems[:name] == ['must be blank']\n").assert_passes();
}
#[test]
fn inclusion_retains_attribute_and_short_message() {
 example(" validates :name, inclusion: { in: ['ready'] }", " t.string :name").run_ruby("w=Widget.new(name: 'other')\nw.valid?\nraise w.problems.inspect unless w.problems[:name] == ['is not included in the list']\n").assert_passes();
}
#[test]
fn format_retains_attribute_and_short_message() {
 example(" validates :name, format: { with: /\\A[a-z]+\\z/ }", " t.string :name").run_ruby("w=Widget.new(name: '123')\nw.valid?\nraise w.problems.inspect unless w.problems[:name] == ['is invalid']\n").assert_passes();
}
#[test]
fn length_minimum_and_maximum_retain_attribute() {
 example(" validates :name, length: { minimum: 3, maximum: 5 }", " t.string :name").run_ruby("a=Widget.new(name: 'x');a.valid?\nb=Widget.new(name: 'xxxxxx');b.valid?\nraise a.problems.inspect unless a.problems[:name] == ['is too short (minimum is 3 characters)']\nraise b.problems.inspect unless b.problems[:name] == ['is too long (maximum is 5 characters)']\n").assert_passes();
}
#[test]
fn numericality_bounds_retain_attribute() {
 example(" validates :amount, numericality: { greater_than: 2, less_than: 4 }", " t.float :amount").run_ruby("a=Widget.new(amount: 2.0);a.valid?\nb=Widget.new(amount: 4.0);b.valid?\nraise a.problems.inspect unless a.problems[:amount] == ['must be greater than 2']\nraise b.problems.inspect unless b.problems[:amount] == ['must be less than 4']\n").assert_passes();
}
#[test]
fn numericality_integer_retains_attribute() {
 example(" validates :amount, numericality: { only_integer: true }", " t.float :amount").run_ruby("w=Widget.new(amount: 1.5);w.valid?\nraise w.problems.inspect unless w.problems[:amount] == ['must be an integer']\n").assert_passes();
}
#[test]
fn secure_password_presence_and_confirmation_retain_attribute() {
 example(" has_secure_password", " t.string :password_digest").run_ruby("require 'bcrypt'\na=Widget.new;a.valid?\nraise a.problems.inspect unless a.problems[:password] == [\"can't be blank\"]\nb=Widget.new(password: 'validpass', password_confirmation: 'different');b.valid?\nraise b.problems.inspect unless b.problems[:password_confirmation] == [\"doesn't match Password\"]\nc=Widget.new(password: 'x' * 73);c.valid?\nraise c.problems.inspect unless c.problems[:password] == ['is too long']\n").assert_passes();
}

#[test]
fn required_association_and_association_presence_retain_attribute() {
 example(" belongs_to :owner\n validates :owner, presence: true", " t.integer :owner_id").run_ruby("w=Widget.new;w.valid?\nraise w.problems.inspect unless w.problems[:owner] == [\"can't be blank\", 'must exist']\n").assert_passes();
}
