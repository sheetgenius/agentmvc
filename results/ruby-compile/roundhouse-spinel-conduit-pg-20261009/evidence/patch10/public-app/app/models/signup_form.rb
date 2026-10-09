class SignupForm
  include ActiveModel::Model
  attr_accessor :name
  def initialize
    @name = ""
  end
  validates :name, presence: true
end
