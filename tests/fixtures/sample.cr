require "./base_action"
require "json"

module Billing
  class Invoice < BaseModel
    include Timestamps
    extend Lookup

    def total(cents : Int64) : Int64
      round_cents(cents)
    end

    def paid? : Bool
      true
    end

    def pay! : Nil
      total(0_i64)
    end

    private def round_cents(value : Int64) : Int64
      value
    end

    def self.build : Invoice
      new
    end
  end

  struct Money
    def zero? : Bool
      true
    end
  end

  enum Status
    Draft
    Paid
  end

  abstract class Repo(T)
    abstract def find(id : Int64) : T
  end
end

class Api::Invoices::Show < ApiAction
  get "/api/invoices/:id" do
    invoice = Billing::Invoice.build
    json({total: invoice.total(1_i64)})
  end
end

def format_cents(cents : Int64) : String
  cents.to_s
end
